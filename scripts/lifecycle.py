#!/usr/bin/env python3
"""Explicit-workspace skill installation, pinned updates and reversible removal."""
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid


def execute(args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=120, **kwargs).stdout


def atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError(f'refusing symlink: {path.name}')
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(text)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def slug_at(root):
    match = re.search(r'^name:\s*([a-z0-9]+(?:-[a-z0-9]+)*)\s*$', (root/'SKILL.md').read_text(), re.M)
    if not match:
        raise ValueError('SKILL.md must have a valid name')
    return match[1]


def workspace(args, root):
    selected = None
    if args.agent:
        raw = execute(['openclaw', 'skills', '--agent', args.agent, 'list', '--json'])
        info = json.loads(raw[raw.index('{'):])
        if not info.get('workspaceDir'):
            raise ValueError('OpenClaw did not report the agent workspace')
        selected = Path(info['workspaceDir']).expanduser().resolve()
    explicit = args.workspace or os.environ.get('OPENCLAW_WORKSPACE')
    if explicit:
        ws = Path(explicit).expanduser().resolve()
        if selected and ws != selected:
            raise ValueError('--workspace does not match --agent')
    elif selected:
        ws = selected
    elif root.parent.name == 'skills':
        ws = root.parent.parent.resolve()
    else:
        raise ValueError('select --workspace DIR or --agent ID explicitly')
    if not ws.is_dir() or ws == Path('/'):
        raise ValueError('workspace must be an existing directory other than /')
    return ws


def validate(root, slug):
    if slug_at(root) != slug:
        raise ValueError('source skill name differs from installed skill')
    for path in root.rglob('*'):
        if any(part in path.parts for part in ('.git','node_modules','__pycache__')):
            continue
        if path.is_symlink():
            raise ValueError('skill source must not contain symlinks')
        if path.is_file() and path.suffix == '.sh':
            execute(['bash', '-n', str(path)])
        elif path.is_file() and path.suffix == '.py':
            compile(path.read_text(), str(path), 'exec')


def inventory(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()
            and not any(part in ('.git', 'node_modules', '__pycache__', '.pytest_cache') for part in p.relative_to(root).parts)}


def replace_block(text, slug, replacement):
    begin = f'<!-- BEGIN:{slug} (managed — do not edit between markers) -->'
    end = f'<!-- END:{slug} -->'
    if text.count(begin) != text.count(end) or text.count(begin) > 1:
        raise ValueError('AGENTS.md has malformed or duplicate managed markers')
    if begin in text:
        start, stop = text.index(begin), text.index(end) + len(end)
        if stop < start:
            raise ValueError('AGENTS.md markers are reversed')
        return text[:start] + replacement + text[stop:]
    return text + ('\n' if text and not text.endswith('\n') else '') + replacement + ('\n' if replacement else '')


def status(ws, target, state, slug):
    agents = ws/'AGENTS.md'
    marker = f'<!-- BEGIN:{slug} '
    print(json.dumps({'skill': slug, 'workspace': str(ws), 'installed': target.is_dir(),
                      'instruction_link': agents.is_file() and marker in agents.read_text(),
                      'runtime_verified': False, 'receipt': (state/'receipt.json').exists()}))


def apply(args, root, ws, slug):
    # Serialize with the suite before acquiring the per-skill lock.
    suite_state = ws/'.memory-suite'
    if suite_state.is_symlink():
        raise ValueError('suite state must not be a symlink')
    with contextlib.ExitStack() as stack:
        if suite_state.exists():
            if (suite_state/'install.lock').is_symlink():raise ValueError('suite lock must not be a symlink')
            suite_lock = stack.enter_context((suite_state/'install.lock').open('a'))
            fcntl.flock(suite_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return apply_locked(args, root, ws, slug)


def apply_locked(args, root, ws, slug):
    target = ws/'skills'/slug
    state = ws/'.openclaw-skill-state'/slug
    if (ws/'.openclaw-skill-state').is_symlink() or state.is_symlink():
        raise ValueError('state path must not be a symlink')
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not state.resolve().is_relative_to(ws) or (ws/'skills').is_symlink() or target.is_symlink():
        raise ValueError('workspace skill/state paths must not escape through symlinks')
    with (state/'lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.operation == 'status':
            return status(ws, target, state, slug)
        agents = ws/'AGENTS.md'
        if agents.is_symlink():
            raise ValueError('AGENTS.md must not be a symlink')
        before = agents.read_text() if agents.exists() else None
        suite_file = ws/'.memory-suite/install.json'
        if suite_file.is_symlink():
            raise ValueError('suite receipt must not be a symlink')
        suite_before = suite_file.read_text() if suite_file.exists() else None
        suite = json.loads(suite_before) if suite_before else {}
        suite_owned = suite.get('paths', {}).get(slug)
        if suite_owned:
            if args.operation not in ('install', 'update') or not getattr(args, 'adopt_suite', False):
                raise ValueError('component belongs to memory-suite; install with --adopt-suite after review')
            if Path(suite_owned['path']) != target or suite_owned['hashes'] != inventory(target):
                raise ValueError('suite component changed; reconcile drift before ownership transfer')

        if args.operation == 'uninstall':
            after = replace_block(before or '', slug, '')
            archive = state/('removed-' + uuid.uuid4().hex)
            if target.exists() and not args.keep_code:
                target.rename(archive)
            try:
                if before is not None:
                    atomic_write(agents, after)
            except Exception:
                if archive.exists():
                    archive.rename(target)
                raise
            if not args.keep_code and (state/'receipt.json').exists():
                (state/'receipt.json').rename(state/('uninstalled-receipt-' + uuid.uuid4().hex + '.json'))
            print(json.dumps({'removed': not args.keep_code, 'data_preserved': True, 'archive': str(archive) if archive.exists() else None}))
            return
        if args.operation == 'rollback':
            receipt = json.loads((state/'receipt.json').read_text())
            if not receipt.get('backup'):
                raise ValueError('no previous version available')
            archive = Path(receipt['backup']).resolve()
            if not archive.is_relative_to(state) or not archive.is_dir():
                raise ValueError('no previous version available')
            current = state/('replaced-' + uuid.uuid4().hex)
            # Do not discard owner edits made after the update.
            now = agents.read_text() if agents.exists() else None
            if now != receipt['agents_after']:
                raise ValueError('AGENTS.md changed since update; reconcile before rollback')
            if target.exists():
                target.rename(current)
            archive.rename(target)
            if receipt['agents_before'] is None:
                agents.unlink(missing_ok=True)
            else:
                atomic_write(agents, receipt['agents_before'])
            receipt['backup'] = None
            receipt['files'] = inventory(target)
            receipt['agents_after'] = receipt['agents_before']
            receipt['revision'] = None
            atomic_write(state/'receipt.json', json.dumps(receipt, indent=2))
            print(json.dumps({'rolled_back': True, 'workspace': str(ws)}))
            return
        with tempfile.TemporaryDirectory(prefix='skill-source-') as tmp:
            source = root
            revision = None
            if args.operation == 'update':
                if not args.repo or not args.ref or not re.fullmatch('[0-9a-fA-F]{40}', args.ref):
                    raise ValueError('update requires --repo URL and --ref FULL_COMMIT_SHA')
                repo = args.repo
                if repo.startswith('git:'):
                    repo = repo[4:]
                    if not repo.startswith(('https://', '/')):
                        repo = 'https://github.com/' + repo + '.git'
                if not (repo.startswith('https://') or Path(repo).is_absolute()):
                    raise ValueError('use an HTTPS repository URL or absolute local repository path')
                source = Path(tmp)/'source'
                execute(['git', 'clone', '--quiet', '--no-checkout', '--', repo, str(source)])
                execute(['git', '-C', str(source), 'checkout', '--quiet', '--detach', args.ref])
                revision = execute(['git', '-C', str(source), 'rev-parse', 'HEAD']).strip()
                if revision.lower() != args.ref.lower():
                    raise ValueError('resolved revision differs from requested revision')
            validate(source, slug)
            target.parent.mkdir(parents=True, exist_ok=True)
            previous_receipt = json.loads((state/'receipt.json').read_text()) if (state/'receipt.json').exists() else {}
            backup = None
            replacing = source.resolve() != target.resolve()
            if replacing and target.exists() and inventory(source) == inventory(target):
                replacing = False
            if args.operation == 'update' and target.exists() and not args.force:
                previous = json.loads((state/'receipt.json').read_text()) if (state/'receipt.json').exists() else {}
                if previous.get('files') != inventory(target):
                    raise ValueError('installed code changed or is unmanaged; review drift before --force')
            if replacing and target.exists() and not (args.force or args.operation == 'update' or suite_owned):
                raise ValueError('target already exists; review changes then pass --force')
            # Prepare all text and metadata before the code swap.
            block = (source/'scripts/activation.md').read_text()
            after = before if args.no_agents else replace_block(before or '', slug, block.rstrip())
            if not suite_owned and not replacing and after == before and previous_receipt.get('files') == inventory(target):
                print(json.dumps({'installed': True, 'workspace': str(ws), 'skill': slug, 'unchanged': True, 'runtime_verified': False, 'rollback_available': bool(previous_receipt.get('backup'))}))
                return
            required = sum(p.stat().st_size for p in source.rglob('*') if p.is_file() and not any(x in p.relative_to(source).parts for x in ('.git','node_modules','__pycache__'))) * 2 + 1024 * 1024
            if replacing and shutil.disk_usage(ws).free < required:
                raise ValueError('insufficient disk for staging and rollback')
            stage = state/('stage-' + uuid.uuid4().hex)
            if replacing:
                shutil.copytree(source, stage, ignore=shutil.ignore_patterns('.git', 'node_modules', '__pycache__', '.pytest_cache'))
                if target.exists():
                    backup = state/('backup-' + uuid.uuid4().hex)
                    target.rename(backup)
                try:
                    stage.rename(target)
                except Exception:
                    if backup:
                        backup.rename(target)
                    shutil.rmtree(stage, ignore_errors=True)
                    raise
            try:
                if not args.no_agents:
                    atomic_write(agents, after)
                atomic_write(state/'receipt.json', json.dumps({'skill': slug, 'revision': revision, 'time': time.time(),
                    'backup': str(backup) if backup else None, 'agents_before': before, 'agents_after': after,
                    'files': inventory(target)}, indent=2))
                if suite_owned:
                    # Remove ownership only after code and standalone receipt are durable.
                    suite['paths'].pop(slug)
                    atomic_write(suite_file, json.dumps(suite, indent=2))
            except Exception:
                if previous_receipt:
                    atomic_write(state/'receipt.json', json.dumps(previous_receipt, indent=2))
                else:
                    (state/'receipt.json').unlink(missing_ok=True)
                if suite_before is not None:
                    atomic_write(suite_file, suite_before)
                if replacing:
                    shutil.rmtree(target)
                    if backup:
                        backup.rename(target)
                if before is None:
                    agents.unlink(missing_ok=True)
                else:
                    atomic_write(agents, before)
                raise
            print(json.dumps({'installed': True, 'workspace': str(ws), 'skill': slug, 'revision': revision,
                              'runtime_verified': False, 'rollback_available': backup is not None}))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('operation', choices=['install', 'update', 'uninstall', 'rollback', 'status'])
    p.add_argument('--workspace')
    p.add_argument('--agent')
    p.add_argument('--repo')
    p.add_argument('--ref')
    p.add_argument('--force', action='store_true')
    p.add_argument('--adopt-suite', action='store_true', help='transfer an unchanged suite-owned component to standalone ownership')
    p.add_argument('--no-agents', action='store_true')
    p.add_argument('--keep-code', action='store_true', help='only remove the AGENTS pointer; skill remains discoverable')
    args = p.parse_args()
    root = Path(__file__).resolve().parent.parent
    try:
        apply(args, root, workspace(args, root), slug_at(root))
    except (OSError, ValueError, subprocess.SubprocessError, KeyError, TypeError) as exc:
        # Subprocess stderr can include credentials or private config; omit it.
        message = f'command failed ({type(exc).__name__})' if isinstance(exc, subprocess.SubprocessError) else str(exc)
        print(json.dumps({'ok': False, 'error': message}), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
