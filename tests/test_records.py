"""The records in this copy, and the bundled example, must be valid.

In the template these checks cover the shipped skeleton and the example. In a company copy they
also guard the company's own records, so an invalid record or a stale PROJECTS.md fails the tests
that `ops.py publish` runs before committing.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

import ops  # noqa: E402

EXAMPLE = REPO / "examples" / "harborline-bakery"


class CompanyRecordsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ctx = ops.load_context(REPO)
        self.records = ops.load_records(self.ctx)

    def test_records_have_no_errors(self) -> None:
        issues = ops.validate(self.ctx, self.records, check_paths=False, check_install=False)
        self.assertEqual([str(i) for i in issues if i.level == "error"], [])

    def test_projects_view_is_current(self) -> None:
        if not self.ctx.bootstrapped:
            self.skipTest("the template has no generated PROJECTS.md until init runs")
        current = (REPO / "PROJECTS.md").read_text(encoding="utf-8")
        self.assertEqual(current, ops.render_projects(self.ctx, self.records), "run: python tools/ops.py render")


@unittest.skipUnless(EXAMPLE.exists(), "example removed in this copy")
class ExampleCompanyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ctx = ops.load_context(EXAMPLE)
        self.records = ops.load_records(self.ctx)

    def test_example_is_valid(self) -> None:
        issues = ops.validate(self.ctx, self.records, check_paths=False, check_install=False)
        self.assertEqual([str(i) for i in issues if i.level == "error"], [])

    def test_example_view_is_current(self) -> None:
        current = (EXAMPLE / "PROJECTS.md").read_text(encoding="utf-8")
        self.assertEqual(current, ops.render_projects(self.ctx, self.records))

    def test_example_instructions_are_filled(self) -> None:
        text = (EXAMPLE / "instructions" / "company.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Company instructions: Harborline Bakery Co."))
        self.assertNotIn("{{", text)


if __name__ == "__main__":
    unittest.main()
