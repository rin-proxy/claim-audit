import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def write(root, name, value):
    (root / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def valid_fixture(root):
    write(root, "source-register.json", {"schema": 1, "sources": [
        {"id": "S001", "url": "https://official.example/spec", "title": "Specification", "publisher": "Example Standards", "source_type": "official", "independent_group": "example-spec", "retrieved": True, "accessed_at": "2026-09-23T00:00:00Z"},
        {"id": "S002", "url": "https://news.example/report", "title": "Independent report", "publisher": "Example News", "source_type": "independent_reporting", "independent_group": "news-report", "retrieved": True, "accessed_at": "2026-09-23T00:01:00Z"}
    ]})
    write(root, "claim-ledger.json", {"schema": 1, "claims": [
        {"id": "C001", "text": "The specification defines a 30 day period.", "kind": "current_fact", "status": "verified", "checked_at": "2026-09-23T00:02:00Z", "citations": ["S001"], "evidence": [{"source_id": "S001", "relation": "supports", "locator": "Section 2", "excerpt": "The period is 30 days."}]},
        {"id": "C002", "text": "The reported outcome remains disputed.", "kind": "fact", "status": "conflicted", "citations": ["S001", "S002"], "evidence": [{"source_id": "S001", "relation": "supports", "locator": "Section 3", "excerpt": "Outcome A."}, {"source_id": "S002", "relation": "contradicts", "locator": "Paragraph 4", "excerpt": "Outcome B."}]}
    ]})
    write(root, "contradictions.json", {"schema": 1, "contradictions": [{"id": "X001", "claim_ids": ["C002"], "source_ids": ["S001", "S002"], "summary": "The sources report different outcomes.", "resolution_status": "unresolved", "disclosed_in_report": True}]})
    (root / "report.md").write_text("# Report\n\nThe current period is 30 days. [C001][S001]\n\n[conflicted] Sources report different outcomes. [C002][S001][S002]\n", encoding="utf-8")


class ValidationTests(unittest.TestCase):
    def run_script(self, name, root):
        return subprocess.run([sys.executable, str(ROOT / "scripts" / name), str(root)], capture_output=True, text=True, timeout=20)

    def test_valid_research_passes_and_writes_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            valid_fixture(root)
            result = self.run_script("validate-ledger.py", root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result = self.run_script("audit-report.py", root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(json.loads((root / "final-audit.json").read_text())["passed"])

    def test_repeated_origin_does_not_verify_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            valid_fixture(root)
            sources = json.loads((root / "source-register.json").read_text())
            sources["sources"][0]["source_type"] = "independent_reporting"
            sources["sources"][1]["independent_group"] = "example-spec"
            write(root, "source-register.json", sources)
            claims = json.loads((root / "claim-ledger.json").read_text())
            claims["claims"][0]["citations"] = ["S001", "S002"]
            claims["claims"][0]["evidence"].append({"source_id": "S002", "relation": "supports", "locator": "Paragraph 2", "excerpt": "Thirty days."})
            write(root, "claim-ledger.json", claims)
            result = self.run_script("validate-ledger.py", root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("two independent eligible groups", result.stdout)

    def test_missing_adjacent_citation_fails_report_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            valid_fixture(root)
            (root / "report.md").write_text("# Report\n\nThe current period is 30 days. [C001]\n\n[conflicted] Different outcomes. [C002][S001][S002]\n")
            result = self.run_script("audit-report.py", root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not adjacent", result.stdout)

    def test_unregistered_url_fails_report_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            valid_fixture(root)
            with (root / "report.md").open("a", encoding="utf-8") as stream:
                stream.write("\nSee https://unregistered.example/page.\n")
            result = self.run_script("audit-report.py", root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unregistered URL", result.stdout)

    def test_initializer_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "research"
            first = self.run_script("init-research.py", root)
            second = self.run_script("init-research.py", root)
            self.assertEqual(first.returncode, 0)
            self.assertNotEqual(second.returncode, 0)


if __name__ == "__main__":
    unittest.main()
