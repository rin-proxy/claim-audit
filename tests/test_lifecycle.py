import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent


class Lifecycle(unittest.TestCase):
    def call(self, root, op, ws, *extra, success=True):
        p = subprocess.run(['bash', str(root/'scripts'/f'{op}.sh'), '--workspace', str(ws), *map(str, extra)], capture_output=True, text=True)
        self.assertEqual(p.returncode == 0, success, p.stdout + p.stderr)
        return p

    def test_lifecycle(self):
        with tempfile.TemporaryDirectory(prefix='skill lifecycle ') as temp:
            base = Path(temp)
            ws = base/'agent workspace';ws.mkdir()
            (ws/'memory').mkdir();(ws/'memory/owner.md').write_text('owner data')
            (ws/'AGENTS.md').write_text('Owner instructions\n')
            self.call(ROOT,'install',ws)
            slug = next(p.name for p in (ws/'skills').iterdir())
            target = ws/'skills'/slug
            self.assertEqual((ws/'AGENTS.md').read_text(),'Owner instructions\n')
            self.call(ROOT,'install',ws,'--legacy-agents-pointer')
            self.assertEqual((ws/'AGENTS.md').read_text().count('<!-- BEGIN:'),1)
            source=base/'origin';shutil.copytree(target,source)
            def git(*args):
                return subprocess.run(['git','-C',str(source),*args],check=True,capture_output=True,text=True).stdout.strip()
            git('init','-q');git('config','user.name','Fixture');git('config','user.email','fixture@example.invalid')
            (source/'revision-proof.txt').write_text('new version')
            git('add','.');git('commit','-qm','Fixture update');sha=git('rev-parse','HEAD')
            self.call(target,'update',ws,'--repo',source,'--ref',sha)
            self.assertTrue((target/'revision-proof.txt').exists())
            self.call(target,'install',ws)  # reinstall must retain the update rollback
            self.call(target,'rollback',ws)
            self.assertFalse((target/'revision-proof.txt').exists())
            receipt=json.loads((ws/'.openclaw-skill-state'/slug/'receipt.json').read_text())
            self.assertNotIn('revision-proof.txt',receipt['files'])
            self.assertEqual((ws/'memory/owner.md').read_text(),'owner data')
            self.call(target,'update',ws,'--repo',source,'--ref','main',success=False)
            self.call(target,'uninstall',ws)
            self.assertFalse(target.exists())
            self.assertNotIn('<!-- BEGIN:',(ws/'AGENTS.md').read_text())
            self.assertEqual((ws/'memory/owner.md').read_text(),'owner data')

    def test_failed_code_swap_restores_previous_code(self):
        import importlib.util, types
        from unittest.mock import patch
        spec=importlib.util.spec_from_file_location('life',ROOT/'scripts/lifecycle.py');life=importlib.util.module_from_spec(spec);spec.loader.exec_module(life)
        with tempfile.TemporaryDirectory() as d:
            ws=Path(d);slug=life.slug_at(ROOT);target=ws/'skills'/slug;target.mkdir(parents=True);(target/'owner-code').write_text('original')
            (ws/'AGENTS.md').write_text('owner instructions')
            args=types.SimpleNamespace(operation='install',force=True,no_agents=False)
            original=Path.rename
            def rename(path,destination):
                if path.name.startswith('stage-'):raise OSError('synthetic code-swap failure')
                return original(path,destination)
            with patch.object(Path,'rename',rename):
                with self.assertRaises(OSError):life.apply(args,ROOT,ws,slug)
            self.assertEqual((target/'owner-code').read_text(),'original')
            self.assertEqual((ws/'AGENTS.md').read_text(),'owner instructions')

    def test_bad_markers_ignored_by_default_and_refused_when_managed(self):
        with tempfile.TemporaryDirectory() as temp:
            ws=Path(temp)
            import re
            slug=re.search(r'^name:\s*(\S+)',(ROOT/'SKILL.md').read_text(),re.M)[1]
            text=f'Owner\n<!-- BEGIN:{slug} (managed — do not edit between markers) -->\n'
            (ws/'AGENTS.md').write_text(text)
            self.call(ROOT,'install',ws)
            self.assertEqual((ws/'AGENTS.md').read_text(),text)
            self.assertTrue((ws/'skills'/slug).exists())
            self.call(ROOT,'install',ws,'--remove-legacy-agents-pointer',success=False)


if __name__ == '__main__':
    unittest.main()
