import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


UPDATE = load("claim_audit_update", ROOT / "scripts/check-update.py")
EXPORT = ROOT / "scripts/export-customizations.py"


class DistributionTools(unittest.TestCase):
    def test_update_check_uses_immutable_commit(self):
        release = {
            "tag_name": "v2.2.0",
            "html_url": "https://github.com/rin-proxy/claim-audit/releases/tag/v2.2.0",
            "commit": "a" * 40,
        }
        result = UPDATE.build_result("2.1.0", "rin-proxy/claim-audit", release)
        self.assertTrue(result["update_available"])
        self.assertEqual(result["latest_version"], "2.2.0")
        self.assertIn("--ref " + "a" * 40, result["update_command"])

    def test_update_check_rejects_moving_ref(self):
        release = {"tag_name": "v2.2.0", "html_url": "https://example.invalid", "commit": "main"}
        with self.assertRaises(ValueError):
            UPDATE.build_result("2.1.0", "rin-proxy/claim-audit", release)

    def test_export_preserves_modified_files_and_deleted_manifest(self):
        with tempfile.TemporaryDirectory(prefix="claim-audit-export-") as raw:
            base = Path(raw)
            workspace = base / "workspace"
            workspace.mkdir()
            process = subprocess.run(
                ["bash", str(ROOT / "scripts/install.sh"), "--workspace", str(workspace)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            target = workspace / "skills" / "claim-audit"
            (target / "README.md").write_text("local README\n")
            (target / "local-note.txt").write_text("local note\n")
            (target / "NOTICE").unlink()
            output = base / "customizations.tar.gz"
            process = subprocess.run(
                [sys.executable, str(EXPORT), "--workspace", str(workspace), "--output", str(output)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            result = json.loads(process.stdout)
            self.assertEqual(result["added"], ["local-note.txt"])
            self.assertEqual(result["modified"], ["README.md"])
            self.assertEqual(result["deleted"], ["NOTICE"])
            with tarfile.open(output, "r:gz") as archive:
                names = set(archive.getnames())
                self.assertIn("claim-audit-customizations/manifest.json", names)
                self.assertIn("claim-audit-customizations/files/README.md", names)
                self.assertIn("claim-audit-customizations/files/local-note.txt", names)


if __name__ == "__main__":
    unittest.main()
