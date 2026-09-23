import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evaluations/20260923"


class EvaluationEvidence(unittest.TestCase):
    def test_matrix_and_summary_match(self):
        cases = json.loads((EVIDENCE / "cases.json").read_text())["cases"]
        rows = json.loads((EVIDENCE / "results.json").read_text())["rows"]
        summary = json.loads((EVIDENCE / "summary.json").read_text())

        self.assertEqual(len(cases), 20)
        self.assertEqual(sum(case["heldout"] for case in cases), 10)
        self.assertEqual(len(rows), 120)
        identities = {(row["case"], row["repetition"], row["arm"]) for row in rows}
        self.assertEqual(len(identities), 120)
        self.assertEqual({row["case"] for row in rows}, {case["id"] for case in cases})

        for arm in ("before", "after"):
            subset = [row for row in rows if row["arm"] == arm]
            valid = [row for row in subset if row["valid_runtime"]]
            published = summary["arms"][arm]
            self.assertEqual(len(subset), published["attempts"])
            self.assertEqual(len(valid), published["valid"])
            self.assertEqual(sum(row["passed"] for row in subset), published["strict_passed"])
            self.assertEqual(
                sum(row["artifact_audit_passed"] for row in valid),
                published["artifact_audit_passed"],
            )
            self.assertEqual(
                sum(row["checks"]["sources_preserved"] for row in subset),
                published["sources_preserved"],
            )

    def test_sanitized_results_exclude_credentials_and_raw_trace(self):
        text = (EVIDENCE / "results.json").read_text()
        github_prefix = r"github" + r"_pat_"
        self.assertNotRegex(text, re.compile(github_prefix + r"|gh[pousr]_[A-Za-z0-9_]{20,}"))
        self.assertNotRegex(text, re.compile(r"sk-[A-Za-z0-9_.-]{20,}"))
        self.assertNotIn('"access_token"', text)
        self.assertNotIn('"refresh_token"', text)
        self.assertNotIn('"trace"', text)
        rows = json.loads(text)["rows"]
        for row in rows:
            self.assertNotIn("answer", row)
            self.assertNotIn("skill_reads", row)
            self.assertNotIn("artifact_audit_output", row)


if __name__ == "__main__":
    unittest.main()
