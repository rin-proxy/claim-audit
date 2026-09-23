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

    def test_install_update_rollback_uninstall_preserves_owner_data(self):
        with tempfile.TemporaryDirectory(prefix='research verifier lifecycle ') as temp:
            base = Path(temp)
            ws = base/'agent workspace';ws.mkdir()
            (ws/'memory').mkdir();(ws/'memory/owner.md').write_text('owner data')
            (ws/'AGENTS.md').write_text('Owner instructions\n')
            self.call(ROOT,'install',ws)
            target = ws/'skills'/'research-verifier'
            self.call(ROOT,'install',ws)
            self.assertEqual((ws/'AGENTS.md').read_text().count('<!-- BEGIN:'),1)
            source=base/'origin';shutil.copytree(target,source)
            def git(*args):
                return subprocess.run(['git','-C',str(source),*args],check=True,capture_output=True,text=True).stdout.strip()
            git('init','-q');git('config','user.name','Fixture');git('config','user.email','fixture@example.invalid')
            (source/'revision-proof.txt').write_text('new version')
            git('add','.');git('commit','-qm','Fixture update');sha=git('rev-parse','HEAD')
            self.call(target,'update',ws,'--repo',source,'--ref',sha)
            self.assertTrue((target/'revision-proof.txt').exists())
            self.call(target,'rollback',ws)
            self.assertFalse((target/'revision-proof.txt').exists())
            receipt=json.loads((ws/'.openclaw-skill-state/research-verifier/receipt.json').read_text())
            self.assertNotIn('revision-proof.txt',receipt['files'])
            self.assertEqual((ws/'memory/owner.md').read_text(),'owner data')
            self.call(target,'update',ws,'--repo',source,'--ref','main',success=False)
            self.call(target,'uninstall',ws)
            self.assertFalse(target.exists())
            self.assertNotIn('<!-- BEGIN:',(ws/'AGENTS.md').read_text())
            self.assertEqual((ws/'memory/owner.md').read_text(),'owner data')


if __name__ == '__main__':
    unittest.main()
