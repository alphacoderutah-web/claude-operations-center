"""Tests for tools/ops.py (stdlib unittest; pytest also collects them).

Run from the repository root: python -m unittest discover -s tests -t tests
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

import ops  # noqa: E402

NOW = datetime(2026, 9, 16, 12, 0, tzinfo=timezone(timedelta(hours=-5)))


TEST_UPSTREAM = "https://github.com/example-org/claude-operations-center"


class Workspace:
    """A scratch, uninitialized company workspace.

    It never reads this repository's own config or records, which in a company copy are the
    company's real data; only the templates are copied.
    """

    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tmp.name) / "company"
        self.root = self.workspace / "ops"
        (self.root / "registry").mkdir(parents=True)
        (self.root / "state").mkdir()
        shutil.copytree(REPO / "templates", self.root / "templates")
        ops.write_json(self.root / "ops.config.json", {
            "schema_version": 1,
            "company": {"name": "Your Company", "timezone": "UTC"},
            "workspace": {"root": "..", "projects_dir": "Projects"},
            "functions": {"operations": "Operations", "money": "Money"},
            "standing_skills": ["agency-conduct"],
            "instructions": {"source": "instructions/company.md",
                             "install_to": str(self.workspace / "installed" / "CLAUDE.md")},
            "template": {"upstream_url": TEST_UPSTREAM, "bootstrapped": False},
        })
        for rel, key in (("registry/projects.json", "projects"), ("registry/automations.json", "automations"),
                         ("registry/assets.json", "assets"), ("registry/access.json", "services"),
                         ("state/observations.json", "observations"), ("state/queue.json", "items")):
            ops.write_json(self.root / rel, {key: []})
        ops.write_json(self.root / "registry" / "systems.json", {"systems": [], "shared_surfaces": []})
        (self.root / "state" / "history.jsonl").write_text("", encoding="utf-8")

    def ctx(self) -> ops.Context:
        return ops.load_context(self.root)

    def write(self, rel: str, data: dict) -> None:
        ops.write_json(self.root / rel, data)

    def seed(self) -> None:
        """Two projects, one automation, one asset, one system, one access record, one observation, one item."""
        self.write("registry/systems.json", {"systems": [{"id": "pos", "name": "POS", "authoritative_for": ["orders"]}], "shared_surfaces": []})
        self.write("registry/assets.json", {"assets": [{"id": "store-a", "name": "Store A", "status": "active"}]})
        self.write("registry/access.json", {"services": [{"id": "pos-api", "service": "POS API", "system": "pos", "mechanism": "token",
                                                           "stored_in": "Projects/Alpha/.env (not read)", "renewal": "regenerate"}]})
        self.write("registry/projects.json", {"projects": [
            {"id": "alpha", "name": "Alpha", "function": "operations", "classification": "business", "lifecycle": "scheduled",
             "purpose": "Imports orders.", "path": "Projects/Alpha", "systems": [{"system": "pos", "modes": ["read"]}],
             "automations": ["win:Alpha Sync"]},
            {"id": "beta", "name": "Beta", "function": "money", "classification": "business", "lifecycle": "live",
             "purpose": "Reconciles deposits.", "path": "Projects/Beta",
             "depends_on": [{"project": "alpha", "kind": "data", "detail": "reads imported orders"}]},
        ]})
        self.write("registry/automations.json", {"automations": [
            {"id": "win:Alpha Sync", "kind": "windows-task", "project": "alpha", "cadence": "every 10 min", "runs_signed_out": True,
             "needs_browser": "none", "enabled": True, "pause": "ops.py pause --project alpha --apply", "access": ["pos-api"]},
        ]})
        self.write("state/observations.json", {"observations": [
            {"id": "alpha-runs", "subject": "alpha", "status": "ok", "statement": "All runs succeeded",
             "checked_at": "2026-09-16T10:00:00-05:00", "ttl_hours": 3, "evidence": ["Projects/Alpha/logs/runs.jsonl"]},
        ]})
        self.write("state/queue.json", {"items": [
            {"id": "q-001", "title": "Renew permit", "kind": "deadline", "priority": "P1", "status": "open", "owner": "owner",
             "due": "2026-10-01", "subjects": ["store-a"], "created_at": "2026-09-16T10:00:00-05:00", "next_step": "Owner pays the fee."},
        ]})
        for name in ("Alpha", "Beta"):
            (self.workspace / "Projects" / name).mkdir(parents=True, exist_ok=True)

    def close(self) -> None:
        self._tmp.cleanup()


def errors(issues: list[ops.Issue]) -> list[str]:
    return [str(i) for i in issues if i.level == "error"]


class TemplateSkeletonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ctx = ops.load_context(REPO)
        if self.ctx.bootstrapped:
            self.skipTest("this is a company copy, not the template")

    def test_shipped_records_are_empty(self) -> None:
        self.assertEqual(ops.load_records(self.ctx).projects, [])

    def test_empty_registry_renders_a_hint(self) -> None:
        self.assertIn("No projects are registered yet", ops.render_projects(self.ctx, ops.load_records(self.ctx)))


class InitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ws = Workspace()
        self.addCleanup(self.ws.close)

    def test_init_configures_and_writes_company_files(self) -> None:
        written = ops.initialize(self.ws.ctx(), "Acme Tools LLC", "America/Chicago",
                                 functions={"shop": "Shop floor", "money": "Money"})
        ctx = self.ws.ctx()
        self.assertTrue(ctx.bootstrapped)
        self.assertEqual(ctx.company, "Acme Tools LLC")
        self.assertEqual(ctx.functions, {"shop": "Shop floor", "money": "Money"})
        instructions = ctx.instructions_source.read_text(encoding="utf-8")
        self.assertTrue(instructions.startswith("# Company instructions: Acme Tools LLC"))
        self.assertIn("America/Chicago", instructions)
        self.assertNotIn("{{", instructions)
        self.assertIn(str(self.ws.workspace / "Projects"), instructions)
        self.assertNotIn("{{", (self.ws.root / "COMPANY.md").read_text(encoding="utf-8"))
        self.assertIn("Projects: Acme Tools LLC", (self.ws.root / "PROJECTS.md").read_text(encoding="utf-8"))
        self.assertIn("instructions/company.md", written)
        history = ops.load_jsonl(self.ws.root / "state" / "history.jsonl")
        self.assertIn("Acme Tools LLC", history[-1]["summary"])

    def test_init_keeps_edited_files_unless_forced(self) -> None:
        ops.initialize(self.ws.ctx(), "Acme", "UTC")
        company = self.ws.root / "COMPANY.md"
        company.write_text("# Edited\n", encoding="utf-8")
        ops.initialize(self.ws.ctx(), "Acme", "UTC")
        self.assertEqual(company.read_text(encoding="utf-8"), "# Edited\n")
        ops.initialize(self.ws.ctx(), "Acme", "UTC", force=True)
        self.assertIn("# Company: Acme", company.read_text(encoding="utf-8"))

    def test_init_rejects_bad_function_ids(self) -> None:
        args = argparse.Namespace(company="Acme", timezone="UTC", workspace_root=None, projects_dir=None,
                                  function=["Bad Id=Title"], install_to=None, force=False)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(ops.cmd_init(self.ws.ctx(), args), 1)
        self.assertFalse(self.ws.ctx().bootstrapped)


class ValidateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ws = Workspace()
        self.addCleanup(self.ws.close)
        self.ws.seed()

    def check(self, check_paths: bool = True) -> list[ops.Issue]:
        ctx = self.ws.ctx()
        return ops.validate(ctx, ops.load_records(ctx), check_paths=check_paths, check_install=False)

    def edit(self, rel: str, change) -> None:
        data = ops.load_json(self.ws.root / rel)
        change(data)
        ops.write_json(self.ws.root / rel, data)

    def test_seeded_records_are_clean(self) -> None:
        self.assertEqual([str(i) for i in self.check()], [])

    def test_unknown_dependency_is_an_error(self) -> None:
        self.edit("registry/projects.json", lambda d: d["projects"][1]["depends_on"][0].update(project="gamma"))
        self.assertTrue(any("gamma" in e for e in errors(self.check())))

    def test_unknown_function_is_an_error(self) -> None:
        self.edit("registry/projects.json", lambda d: d["projects"][0].update(function="catering"))
        self.assertTrue(any("unknown function 'catering'" in e for e in errors(self.check())))

    def test_missing_path_is_only_a_warning(self) -> None:
        self.edit("registry/projects.json", lambda d: d["projects"][0].update(path="Projects/Moved"))
        issues = self.check()
        self.assertEqual([i.level for i in issues], ["warning"])

    def test_duplicate_ids_are_errors(self) -> None:
        self.edit("registry/projects.json", lambda d: d["projects"].append(dict(d["projects"][0])))
        self.assertTrue(any("duplicate id 'alpha'" in e for e in errors(self.check(check_paths=False))))

    def test_observations_need_offset_and_ttl(self) -> None:
        def change(d):
            d["observations"][0]["checked_at"] = "2026-09-16T10:00:00"
            del d["observations"][0]["ttl_hours"]
        self.edit("state/observations.json", change)
        found = errors(self.check(check_paths=False))
        self.assertTrue(any("without offset" in e for e in found))
        self.assertTrue(any("missing 'ttl_hours'" in e for e in found))

    def test_open_items_need_a_next_step(self) -> None:
        self.edit("state/queue.json", lambda d: d["items"][0].pop("next_step"))
        self.assertTrue(any("need a next_step" in e for e in errors(self.check(check_paths=False))))

    def test_unlisted_automation_is_a_warning(self) -> None:
        self.edit("registry/projects.json", lambda d: d["projects"][0].update(automations=[]))
        issues = self.check(check_paths=False)
        self.assertEqual([(i.level, i.message) for i in issues], [("warning", "not listed by its project")])

    def test_automation_ids_need_a_kind_prefix(self) -> None:
        def change(d):
            d["automations"][0]["id"] = "Alpha Sync"
        self.edit("registry/automations.json", change)
        self.edit("registry/projects.json", lambda d: d["projects"][0].update(automations=["Alpha Sync"]))
        self.assertTrue(any("kind-prefix" in e for e in errors(self.check(check_paths=False))))


class SecretScanTests(unittest.TestCase):
    def scan(self, text: str, folder: str = "procedures") -> list[ops.Issue]:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / folder).mkdir()
        (root / folder / "note.md").write_text(text, encoding="utf-8")
        return ops.scan_for_secrets(root)

    def test_token_shapes_are_flagged(self) -> None:
        for sample in ("ghp_" + "a" * 36, "sk-ant-" + "b" * 30, "api_key = " + "c" * 24):
            with self.subTest(sample=sample[:8]):
                self.assertTrue(self.scan(f"value {sample}\n"))

    def test_card_numbers_need_a_valid_checksum(self) -> None:
        prefix = "4111 1111 1111 "  # built at runtime so this file passes the scan itself
        self.assertTrue(self.scan(f"card {prefix}1111\n"))
        self.assertFalse(self.scan(f"order {prefix}1112\n"))

    def test_ssn_shapes_are_flagged(self) -> None:
        self.assertTrue(self.scan("id " + "-".join(("123", "45", "6789")) + "\n"))

    def test_ordinary_prose_passes(self) -> None:
        self.assertFalse(self.scan("The token is stored in Projects/Alpha/.env and never read.\n"))

    def test_evidence_folder_is_skipped(self) -> None:
        self.assertFalse(self.scan("ghp_" + "a" * 36, folder="evidence"))

    def test_this_repository_is_clean(self) -> None:
        self.assertEqual([str(i) for i in ops.scan_for_secrets(REPO)], [])


class ViewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ws = Workspace()
        self.addCleanup(self.ws.close)
        self.ws.seed()
        self.ctx = self.ws.ctx()
        self.records = ops.load_records(self.ctx)

    def test_stale_observation_reads_as_unknown(self) -> None:
        obs = self.records.observations[0]
        self.assertEqual(ops.effective_status(obs, NOW), "ok")
        self.assertEqual(ops.effective_status(obs, NOW + timedelta(hours=5)), "unknown")

    def test_projects_view_is_deterministic_and_complete(self) -> None:
        text = ops.render_projects(self.ctx, self.records)
        self.assertEqual(text, ops.render_projects(self.ctx, self.records))
        self.assertIn("**Alpha** `alpha`", text)
        self.assertIn("ok (2026-09-16)", text)
        self.assertIn("unknown (never checked)", text)
        self.assertIn("| Beta | Alpha | data | reads imported orders |", text)
        self.assertIn("`win:Alpha Sync`", text)

    def test_status_view_marks_stale_and_lists_open_work(self) -> None:
        text = ops.render_status(self.records, NOW + timedelta(hours=5))
        self.assertIn("[UNKNOWN  ] Alpha", text)
        self.assertIn("stale", text)
        self.assertIn("P1 deadline", text)
        self.assertIn("due 2026-10-01", text)


class NewProjectTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ws = Workspace()
        self.addCleanup(self.ws.close)
        ops.initialize(self.ws.ctx(), "Acme", "UTC")

    def add(self, **overrides):
        args = {"project_id": "inventory-report", "name": "Inventory Report", "function": "operations",
                "purpose": "Builds a weekly inventory report per store."}
        args.update(overrides)
        return ops.add_project(self.ws.ctx(), **args)

    def test_registers_and_scaffolds(self) -> None:
        entry, created = self.add()
        folder = self.ws.workspace / "Projects" / "Inventory Report"
        self.assertEqual(entry["path"], "Projects/Inventory Report")
        claude_md = (folder / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("# Inventory Report", claude_md)
        self.assertIn("Builds a weekly inventory report per store.", claude_md)
        self.assertIn("Company: Acme", claude_md)
        self.assertNotIn("{{", claude_md)
        self.assertTrue((folder / ".gitignore").read_text(encoding="utf-8").startswith("# Secrets"))
        self.assertEqual(len(created), 3)
        ctx = self.ws.ctx()
        records = ops.load_records(ctx)
        self.assertEqual(errors(ops.validate(ctx, records, check_install=False)), [])
        self.assertEqual(ops.load_jsonl(self.ws.root / "state" / "history.jsonl")[-1]["subject"], "inventory-report")

    def test_invalid_entries_write_nothing(self) -> None:
        self.add(project_id="existing", name="Existing")
        for overrides in ({"project_id": "existing"}, {"project_id": "Bad Id"}, {"function": "catering"}):
            with self.subTest(**overrides):
                with self.assertRaises(ValueError):
                    self.add(**overrides)
        self.assertEqual([p["id"] for p in ops.load_records(self.ws.ctx()).projects], ["existing"])
        self.assertFalse((self.ws.workspace / "Projects" / "Inventory Report").exists())

    def test_existing_project_files_are_kept(self) -> None:
        folder = self.ws.workspace / "Projects" / "Inventory Report"
        folder.mkdir(parents=True)
        (folder / "CLAUDE.md").write_text("# Mine\n", encoding="utf-8")
        _, created = self.add()
        self.assertEqual((folder / "CLAUDE.md").read_text(encoding="utf-8"), "# Mine\n")
        self.assertEqual(created, [str(folder / ".gitignore")])


class InstallTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ws = Workspace()
        self.addCleanup(self.ws.close)

    def run_install(self, check: bool = False) -> int:
        with contextlib.redirect_stdout(io.StringIO()):
            return ops.cmd_install(self.ws.ctx(), argparse.Namespace(check=check))

    def test_install_before_init_fails(self) -> None:
        self.assertEqual(self.run_install(), 1)

    def test_install_copies_and_reports_drift(self) -> None:
        ops.initialize(self.ws.ctx(), "Acme", "UTC")
        ctx = self.ws.ctx()
        self.assertIn("not installed", ops.instructions_drift(ctx))
        self.assertEqual(self.run_install(check=True), 1)
        self.assertEqual(self.run_install(), 0)
        self.assertEqual(ctx.instructions_target.read_bytes(), ctx.instructions_source.read_bytes())
        self.assertIsNone(ops.instructions_drift(ctx))
        ctx.instructions_target.write_text("# Old\n", encoding="utf-8")
        self.assertIn("differs", ops.instructions_drift(ctx))
        self.assertEqual(self.run_install(), 0)
        backups = list(ctx.instructions_target.parent.glob("CLAUDE.md.bak-*"))
        self.assertEqual(len(backups), 1)


@unittest.skipUnless(shutil.which("git"), "git is not installed")
class PublishGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ws = Workspace()
        self.addCleanup(self.ws.close)
        subprocess.run(["git", "init", "-q", str(self.ws.root)], check=True)

    def set_origin(self, url: str) -> None:
        subprocess.run(["git", "-C", str(self.ws.root), "remote", "add", "origin", url], check=True)

    def publish(self) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = ops.cmd_publish(self.ws.ctx(), argparse.Namespace(message="test"))
        return code, out.getvalue()

    def test_uninitialized_copy_is_refused(self) -> None:
        code, text = self.publish()
        self.assertEqual(code, 1)
        self.assertIn("not initialized", text)

    def test_template_origin_is_refused_in_any_url_form(self) -> None:
        ops.initialize(self.ws.ctx(), "Acme", "UTC")
        upstream = self.ws.ctx().template_upstream
        ssh = upstream.replace("https://github.com/", "git@github.com:") + ".git"
        self.set_origin(ssh)
        self.assertTrue(ops.origin_is_template(self.ws.ctx()))
        code, text = self.publish()
        self.assertEqual(code, 1)
        self.assertIn("public template", text)

    def test_company_origin_is_not_the_template(self) -> None:
        ops.initialize(self.ws.ctx(), "Acme", "UTC")
        self.set_origin("https://github.com/acme/acme-ops.git")
        self.assertFalse(ops.origin_is_template(self.ws.ctx()))


class PauseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ws = Workspace()
        self.addCleanup(self.ws.close)
        self.ws.seed()

    def pause(self, **kwargs) -> tuple[int, str]:
        args = argparse.Namespace(project="alpha", resume=False, apply=False)
        for key, value in kwargs.items():
            setattr(args, key, value)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = ops.cmd_pause(self.ws.ctx(), args)
        return code, out.getvalue()

    def test_plan_changes_nothing(self) -> None:
        code, text = self.pause()
        self.assertEqual(code, 0)
        self.assertIn("WOULD PAUSE", text)
        self.assertIn("nothing changed", text)

    def test_unknown_project_fails(self) -> None:
        code, _ = self.pause(project="nobody")
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
