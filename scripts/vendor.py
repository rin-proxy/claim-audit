#!/usr/bin/env python3
"""Verify vendored files offline, or regenerate one source group from an immutable checkout."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


def safe(root,rel):
    if Path(rel).is_absolute() or '..' in Path(rel).parts:raise ValueError('unsafe vendor path')
    path=root/rel
    if not path.resolve().is_relative_to(root) or any(p.is_symlink() for p in [path,*path.parents] if p.is_relative_to(root)):raise ValueError('symlinked vendor path')
    return path


def check(root):
    manifest=json.loads((root/'vendor.json').read_text())
    failures=[]
    for row in manifest['files']:
        path=safe(root,row['destination'])
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256']:failures.append(row['destination'])
        if row['revision']=='self':
            if row['repository']!=manifest['repository']:raise ValueError('external self reference')
            if safe(root,row['source']).read_bytes()!=path.read_bytes():failures.append('canonical drift: '+row['destination'])
        elif not re.fullmatch('[a-f0-9]{40}',row['revision']):raise ValueError('external revision must be an immutable commit')
    if failures:raise ValueError('vendor drift: '+', '.join(failures))
    return {'status':'OK','files':len(manifest['files'])}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('operation',choices=['check','bundle'])
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent)
    p.add_argument('--source',type=Path);p.add_argument('--repository');p.add_argument('--ref')
    p.add_argument('--map',action='append',default=[],help='source-file=destination-file, repeatable')
    a=p.parse_args();root=a.root.resolve()
    try:
        if a.operation=='check':result=check(root)
        else:
            if not a.source or not re.fullmatch('[a-f0-9]{40}',a.ref or '') or not a.repository or not a.map:raise ValueError('bundle requires source, repository, full ref and mappings')
            source=a.source.resolve()
            def git(*argv):return subprocess.run(['git','-C',str(source),*argv],capture_output=True,check=True,timeout=60).stdout
            if git('rev-parse',a.ref+'^{commit}').decode().strip()!=a.ref:raise ValueError('commit unavailable')
            manifest=json.loads((root/'vendor.json').read_text()) if (root/'vendor.json').exists() else {'schema':1,'repository':root.name,'files':[]}
            prepared=[]
            for mapping in a.map:
                src,dst=mapping.split('=',1);safe(source,src);safe(root,dst)
                blob=git('show',a.ref+':'+src)
                prepared.append((dst,blob,{'repository':a.repository,'revision':a.ref,'source':src,'destination':dst,'sha256':hashlib.sha256(blob).hexdigest()}))
            replaced={dst for dst,_,_ in prepared}
            manifest['files']=[r for r in manifest['files'] if r['destination'] not in replaced]
            for dst,blob,row in prepared:
                path=safe(root,dst);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(blob);manifest['files'].append(row)
            manifest['files'].sort(key=lambda r:r['destination'])
            (root/'vendor.json').write_text(json.dumps(manifest,indent=2)+'\n');result=check(root)
        print(json.dumps(result));return 0
    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as exc:
        print(json.dumps({'status':'FAIL','error':str(exc) if not isinstance(exc,subprocess.SubprocessError) else 'source commit unavailable'}),file=sys.stderr);return 1

if __name__=='__main__':sys.exit(main())
