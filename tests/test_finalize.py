import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
FINALIZE = ROOT / "scripts/finalize-research.py"


def pack(report_text="The documented period is 30 days.", source_type="official"):
    return {
        "schema": 1,
        "plan": {
            "question": "What is the period?",
            "scope": "Synthetic specification",
            "as_of_time": "2026-09-23",
            "completion_rule": "One retrieved official source directly answers the claim.",
        },
        "sources": [{
            "id": "S001",
            "url": "https://standards.example/spec",
            "title": "Synthetic specification",
            "publisher": "Example Standards",
            "source_type": source_type,
            "independent_group": "synthetic-spec",
            "retrieved": True,
            "accessed_at": "2026-09-23T00:00:00Z",
        }],
        "claims": [{
            "id": "C001",
            "text": "The synthetic specification defines a 30 day period.",
            "kind": "fact",
            "status": "verified",
            "citations": ["S001"],
            "evidence": [{
                "source_id": "S001",
                "relation": "supports",
                "locator": "Section 2",
                "excerpt": "The period is 30 days.",
            }],
        }],
        "contradictions": [],
        "report": {
            "title": "Synthetic research report",
            "sections": [{"claim_id": "C001", "text": report_text}],
        },
    }


class FinalizeResearch(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.pack = self.root / "evidence-pack.json"
        self.output = self.root / "research"
        self.write_pack(pack())

    def write_pack(self, value):
        self.pack.write_text(json.dumps(value, indent=2) + "\n")

    def run_finalize(self, *extra):
        return subprocess.run(
            [sys.executable, str(FINALIZE), str(self.pack), str(self.output), *extra],
            capture_output=True,
            text=True,
        )

    def test_single_pack_renders_and_audits(self):
        result = self.run_finalize()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = (self.output / "report.md").read_text()
        self.assertIn("[C001][S001]", report)
        self.assertTrue(json.loads((self.output / "final-audit.json").read_text())["passed"])
        self.assertTrue((self.output / ".claim-audit-render.json").is_file())

    def test_replacement_accepts_legacy_render_manifest(self):
        self.assertEqual(self.run_finalize().returncode, 0)
        current = self.output / ".claim-audit-render.json"
        current.rename(self.output / ".research-verifier-render.json")
        self.write_pack(pack("The current documented period remains 30 days."))
        replaced = self.run_finalize("--replace-managed")
        self.assertEqual(replaced.returncode, 0, replaced.stderr)
        self.assertTrue(current.is_file())

    def test_refuses_overwrite_and_preserves_unrelated_files(self):
        self.assertEqual(self.run_finalize().returncode, 0)
        owner = self.output / "owner.txt"
        owner.write_text("keep")
        self.assertEqual(self.run_finalize().returncode, 2)
        self.write_pack(pack("The current documented period remains 30 days."))
        replaced = self.run_finalize("--replace-managed")
        self.assertEqual(replaced.returncode, 0, replaced.stderr)
        self.assertEqual(owner.read_text(), "keep")
        self.assertIn("remains 30 days", (self.output / "report.md").read_text())

    def test_replacement_refuses_managed_owner_drift(self):
        self.assertEqual(self.run_finalize().returncode, 0)
        (self.output / "report.md").write_text("owner edit")
        self.write_pack(pack("Replacement text."))
        result = self.run_finalize("--replace-managed")
        self.assertEqual(result.returncode, 2)
        self.assertIn("owner drift", result.stderr)
        self.assertEqual((self.output / "report.md").read_text(), "owner edit")

    def test_rejects_incomplete_report_sections_before_writing(self):
        value = pack()
        value["report"]["sections"] = []
        self.write_pack(value)
        result = self.run_finalize()
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.output / "report.md").exists())

    def test_failed_audit_remains_inspectable(self):
        self.write_pack(pack(source_type="community"))
        result = self.run_finalize()
        self.assertEqual(result.returncode, 1)
        audit = json.loads((self.output / "final-audit.json").read_text())
        self.assertFalse(audit["passed"])
        self.assertTrue(any("verified requires" in item for item in audit["errors"]))


if __name__ == "__main__":
    unittest.main()
