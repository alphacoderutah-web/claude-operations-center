"""Operations center records for one company.

One registry of the company's projects, automations, assets, systems and access references, plus
dated observations, a work queue, decisions and history. Every view is generated from the same
JSON, so a daily email or a dashboard can read exactly what Claude reads.

Standard library only (Python 3.10+). Run from the repository root:

    python tools/ops.py init --company NAME --timezone AREA/CITY   set this copy up for a company
    python tools/ops.py status                   what is known, what is stale, what is open
    python tools/ops.py validate [--no-paths]    check registry and state; exit 1 on errors
    python tools/ops.py render [--check]         regenerate PROJECTS.md
    python tools/ops.py new-project --id ID --name NAME --function F --purpose TEXT
    python tools/ops.py observe ID --subject S --status ok|attention|failing|unknown
                         --statement TEXT --evidence REF [--evidence REF ...] --ttl-hours N
    python tools/ops.py record --subject S --summary TEXT [--evidence REF ...]
    python tools/ops.py pause --project ID [--resume] [--apply]
    python tools/ops.py install [--check]        install the company instructions for Claude Code
    python tools/ops.py publish -m MESSAGE       validate, render, test, commit, push

Records never hold secrets or personal data; `validate` rejects credential-shaped text.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

REPO = Path(__file__).resolve().parents[1]
CONFIG_FILE = "ops.config.json"

CLASSIFICATIONS = {"business", "shared-infrastructure", "experiment", "unrelated-venture", "placeholder", "records"}
LIFECYCLES = {"live", "scheduled", "manual", "pilot", "not-configured", "dormant", "complete", "placeholder", "retired"}
ACCESS_MODES = {"read", "write", "charge", "send"}
DEPENDENCY_KINDS = {"code", "data", "external-field", "copied-code", "shared-infra", "lineage", "tooling"}
AUTOMATION_KINDS = {
    "windows-task", "cron", "launchd", "systemd-timer", "always-on-service", "claude-routine",
    "cloud-scheduler", "cloudflare-cron", "github-actions", "saas-automation", "other",
}
BROWSER_NEEDS = {"none", "automation-profile", "owner-browser"}
OBS_STATUSES = ("failing", "attention", "unknown", "ok")
QUEUE_KINDS = {"incident", "deadline", "blocker", "maintenance", "improvement", "decision"}
QUEUE_STATUSES = {"open", "in-progress", "waiting", "done", "dropped"}
QUEUE_OWNERS = {"claude", "owner", "staff", "other-team"}
PRIORITIES = ("P1", "P2", "P3", "P4")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")
AUTOMATION_ID_RE = re.compile(r"^[a-z][a-z0-9-]*:\S.*$")

SECRET_PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9_-]{16,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{30,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    re.compile(r"\b[sr]k_live_[0-9A-Za-z]{16,}"),
    re.compile(r"(?i)\b(password|passwd|secret|api[_-]?key|token)\b\s*[:=]\s*['\"]?[A-Za-z0-9/+_\-]{16,}"),
]
CARD_RE = re.compile(r"\b(?:\d[ -]?){13,19}\b")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
SCANNED_SUFFIXES = {".md", ".json", ".jsonl", ".py", ".txt", ".ps1", ".sh", ".cmd", ".toml", ".yml", ".yaml"}
SCAN_SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "evidence"}


# ---------------------------------------------------------------- context


@dataclass
class Context:
    """One operations repository and its configuration."""

    root: Path
    config: dict

    @property
    def company(self) -> str:
        return self.config["company"]["name"]

    @property
    def timezone_name(self) -> str:
        return self.config["company"].get("timezone", "")

    @property
    def workspace(self) -> Path:
        """The company workspace; registry paths are relative to it."""
        configured = Path(os.path.expanduser(self.config["workspace"].get("root", "..")))
        return configured if configured.is_absolute() else (self.root / configured).resolve()

    @property
    def projects_dir(self) -> str:
        return self.config["workspace"].get("projects_dir", "Projects")

    @property
    def functions(self) -> dict[str, str]:
        return self.config["functions"]

    @property
    def bootstrapped(self) -> bool:
        return bool(self.config.get("template", {}).get("bootstrapped"))

    @property
    def instructions_source(self) -> Path:
        return self.root / self.config["instructions"].get("source", "instructions/company.md")

    @property
    def instructions_target(self) -> Path:
        return Path(os.path.expanduser(self.config["instructions"].get("install_to", "~/.claude/CLAUDE.md")))

    @property
    def template_upstream(self) -> str:
        return self.config.get("template", {}).get("upstream_url", "")


def load_context(root: Path = REPO) -> Context:
    # Resolve once so every path the tool writes uses one spelling (Windows can hand out 8.3 short names).
    root = root.resolve()
    return Context(root=root, config=load_json(root / CONFIG_FILE))


# ---------------------------------------------------------------- files


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Any) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8") as fh:
        for number, line in enumerate(fh, 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path.name} line {number}: {exc}") from exc
    return rows


def fill(template: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


@dataclass
class Records:
    projects: list[dict]
    automations: list[dict]
    assets: list[dict]
    access: list[dict]
    systems: list[dict]
    shared_surfaces: list[dict]
    observations: list[dict]
    queue: list[dict]


def load_records(ctx: Context) -> Records:
    registry, state = ctx.root / "registry", ctx.root / "state"
    systems = load_json(registry / "systems.json")
    return Records(
        projects=load_json(registry / "projects.json")["projects"],
        automations=load_json(registry / "automations.json")["automations"],
        assets=load_json(registry / "assets.json")["assets"],
        access=load_json(registry / "access.json")["services"],
        systems=systems["systems"],
        shared_surfaces=systems.get("shared_surfaces", []),
        observations=load_json(state / "observations.json")["observations"],
        queue=load_json(state / "queue.json")["items"],
    )


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp without offset: {value}")
    return parsed


def now_local() -> datetime:
    return datetime.now(timezone.utc).astimezone()


def resolve_path(ctx: Context, value: str) -> Path:
    candidate = Path(os.path.expanduser(value))
    return candidate if candidate.is_absolute() else ctx.workspace / candidate


# ---------------------------------------------------------------- validation


@dataclass
class Issue:
    level: str  # "error" | "warning"
    where: str
    message: str

    def __str__(self) -> str:
        return f"{self.level.upper():7} {self.where}: {self.message}"


def _require(obj: dict, fields: Iterable[str], where: str, issues: list[Issue]) -> None:
    for name in fields:
        if obj.get(name) in (None, "", []):
            issues.append(Issue("error", where, f"missing '{name}'"))


def _unique(items: list[dict], label: str, issues: list[Issue]) -> set[str]:
    seen: set[str] = set()
    for item in items:
        value = item.get("id")
        if value in seen:
            issues.append(Issue("error", label, f"duplicate id '{value}'"))
        seen.add(value)
    return seen


def _check_time(value: Any, where: str, issues: list[Issue]) -> None:
    if value:
        try:
            parse_time(str(value))
        except ValueError as exc:
            issues.append(Issue("error", where, str(exc)))


def validate(ctx: Context, records: Records, check_paths: bool = True, check_install: bool = True) -> list[Issue]:
    issues: list[Issue] = []
    project_ids = _unique(records.projects, "projects", issues)
    automation_ids = _unique(records.automations, "automations", issues)
    asset_ids = _unique(records.assets, "assets", issues)
    system_ids = _unique(records.systems, "systems", issues)
    access_ids = _unique(records.access, "access", issues)
    subjects = project_ids | automation_ids | asset_ids | system_ids | access_ids | {"company"}

    for system in records.systems:
        _require(system, ("id", "name", "authoritative_for"), f"systems/{system.get('id')}", issues)

    for project in records.projects:
        where = f"projects/{project.get('id')}"
        _require(project, ("id", "name", "function", "classification", "lifecycle", "purpose", "path"), where, issues)
        if not ID_RE.match(str(project.get("id", ""))):
            issues.append(Issue("error", where, "id must be lowercase letters, digits and hyphens"))
        for key, allowed in (("function", ctx.functions), ("classification", CLASSIFICATIONS), ("lifecycle", LIFECYCLES)):
            if project.get(key) not in allowed:
                issues.append(Issue("error", where, f"unknown {key} '{project.get(key)}'"))
        for dep in project.get("depends_on", []):
            if dep.get("project") not in project_ids:
                issues.append(Issue("error", where, f"depends_on unknown project '{dep.get('project')}'"))
            if dep.get("kind") not in DEPENDENCY_KINDS:
                issues.append(Issue("error", where, f"unknown dependency kind '{dep.get('kind')}'"))
        for use in project.get("systems", []):
            if use.get("system") not in system_ids:
                issues.append(Issue("error", where, f"uses unknown system '{use.get('system')}'"))
            for mode in use.get("modes", []):
                if mode not in ACCESS_MODES:
                    issues.append(Issue("error", where, f"unknown access mode '{mode}'"))
        for ref in project.get("automations", []):
            if ref not in automation_ids:
                issues.append(Issue("error", where, f"lists unknown automation '{ref}'"))
        if check_paths:
            paths = [("path", project["path"])] if project.get("path") else []
            if (project.get("repo") or {}).get("path"):
                paths.append(("repo.path", project["repo"]["path"]))
            for label, value in paths:
                if not resolve_path(ctx, value).exists():
                    issues.append(Issue("warning", where, f"{label} does not exist: {value}"))

    listed = {ref for p in records.projects for ref in p.get("automations", [])}
    for automation in records.automations:
        where = f"automations/{automation.get('id')}"
        _require(automation, ("id", "kind", "project", "cadence", "needs_browser", "pause"), where, issues)
        if not AUTOMATION_ID_RE.match(str(automation.get("id", ""))):
            issues.append(Issue("error", where, "id must look like <kind-prefix>:<native name>, e.g. win:Nightly Sync"))
        if automation.get("kind") not in AUTOMATION_KINDS:
            issues.append(Issue("error", where, f"unknown kind '{automation.get('kind')}'"))
        if automation.get("project") not in project_ids:
            issues.append(Issue("error", where, f"unknown project '{automation.get('project')}'"))
        if automation.get("needs_browser") not in BROWSER_NEEDS:
            issues.append(Issue("error", where, f"unknown needs_browser '{automation.get('needs_browser')}'"))
        for ref in automation.get("access", []):
            if ref not in access_ids:
                issues.append(Issue("error", where, f"unknown access record '{ref}'"))
        if automation.get("id") not in listed:
            issues.append(Issue("warning", where, "not listed by its project"))

    for asset in records.assets:
        _require(asset, ("id", "name", "status"), f"assets/{asset.get('id')}", issues)

    for service in records.access:
        where = f"access/{service.get('id')}"
        _require(service, ("id", "service", "mechanism", "stored_in", "renewal"), where, issues)
        if service.get("system") and service["system"] not in system_ids:
            issues.append(Issue("error", where, f"unknown system '{service['system']}'"))

    _unique(records.observations, "observations", issues)
    for obs in records.observations:
        where = f"observations/{obs.get('id')}"
        _require(obs, ("id", "subject", "status", "statement", "checked_at", "evidence", "ttl_hours"), where, issues)
        if obs.get("status") not in OBS_STATUSES:
            issues.append(Issue("error", where, f"unknown status '{obs.get('status')}'"))
        if obs.get("subject") not in subjects:
            issues.append(Issue("error", where, f"unknown subject '{obs.get('subject')}'"))
        _check_time(obs.get("checked_at"), where, issues)

    _unique(records.queue, "queue", issues)
    for item in records.queue:
        where = f"queue/{item.get('id')}"
        _require(item, ("id", "title", "kind", "priority", "status", "owner", "created_at"), where, issues)
        for key, allowed in (("kind", QUEUE_KINDS), ("status", QUEUE_STATUSES), ("owner", QUEUE_OWNERS), ("priority", PRIORITIES)):
            if item.get(key) not in allowed:
                issues.append(Issue("error", where, f"unknown {key} '{item.get(key)}'"))
        if item.get("status") not in {"done", "dropped"} and not item.get("next_step"):
            issues.append(Issue("error", where, "open items need a next_step"))
        for subject in item.get("subjects", []):
            if subject not in subjects:
                issues.append(Issue("error", where, f"unknown subject '{subject}'"))
        _check_time(item.get("created_at"), where, issues)
        if item.get("due"):
            try:
                datetime.strptime(item["due"], "%Y-%m-%d")
            except ValueError:
                issues.append(Issue("error", where, f"due must be YYYY-MM-DD, got '{item['due']}'"))

    try:
        for number, row in enumerate(load_jsonl(ctx.root / "state" / "history.jsonl"), 1):
            _require(row, ("at", "subject", "summary"), f"history line {number}", issues)
    except ValueError as exc:
        issues.append(Issue("error", "history", str(exc)))

    issues.extend(scan_for_secrets(ctx.root))
    if check_install and ctx.bootstrapped:
        drift = instructions_drift(ctx)
        if drift:
            issues.append(Issue("warning", "instructions", drift))
    return issues


def _luhn(digits: str) -> bool:
    total, parity = 0, len(digits) % 2
    for index, char in enumerate(digits):
        value = int(char)
        if index % 2 == parity:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0


def scan_for_secrets(root: Path) -> list[Issue]:
    issues: list[Issue] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SCAN_SKIP_DIRS]
        for name in filenames:
            path = Path(dirpath) / name
            if path.suffix.lower() not in SCANNED_SUFFIXES:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            rel = path.relative_to(root).as_posix()
            for number, line in enumerate(text.splitlines(), 1):
                if any(p.search(line) for p in SECRET_PATTERNS):
                    issues.append(Issue("error", f"{rel}:{number}", "credential-shaped text"))
                for match in CARD_RE.finditer(line):
                    digits = re.sub(r"\D", "", match.group())
                    if 13 <= len(digits) <= 19 and _luhn(digits) and len(set(digits)) > 1:
                        issues.append(Issue("error", f"{rel}:{number}", "card-number-shaped text"))
                if SSN_RE.search(line):
                    issues.append(Issue("error", f"{rel}:{number}", "SSN-shaped text"))
    return issues


# ---------------------------------------------------------------- views


def effective_status(obs: dict, now: datetime) -> str:
    """An observation older than its time-to-live is no longer evidence: it reads as unknown."""
    ttl = obs.get("ttl_hours")
    if ttl is not None and now - parse_time(obs["checked_at"]) > timedelta(hours=float(ttl)):
        return "unknown"
    return obs["status"]


def _worst(statuses: Iterable[str]) -> str:
    present = set(statuses)
    ranked = [s for s in OBS_STATUSES if s in present]
    return ranked[0] if ranked else "unknown"


def _md(text: Any) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def render_projects(ctx: Context, records: Records) -> str:
    projects = {p["id"]: p for p in records.projects}
    by_subject: dict[str, list[dict]] = {}
    for obs in records.observations:
        by_subject.setdefault(obs["subject"], []).append(obs)
    lines = [
        f"# Projects: {ctx.company}",
        "",
        "<!-- Generated by `python tools/ops.py render` from registry/*.json and state/observations.json. Edit those files, not this one. -->",
        "",
        "Every project, automation and cross-project dependency, grouped by business function. Recorded",
        "state carries the date it was checked; `python tools/ops.py status` shows which observations are",
        "still current. Paths are relative to the company workspace unless absolute.",
        "",
    ]
    if not records.projects:
        lines += ["No projects are registered yet. Run the baseline survey (BOOTSTRAP.md, stage 4).", ""]
    for function, title in ctx.functions.items():
        members = [p for p in records.projects if p["function"] == function]
        if not members:
            continue
        lines += [f"## {title}", "", "| Project | Purpose | Lifecycle | Recorded state | Automations |", "|---|---|---|---|---|"]
        for p in members:
            recorded = by_subject.get(p["id"], [])
            if recorded:
                newest = max(recorded, key=lambda o: o["checked_at"])
                state = f"{_worst(o['status'] for o in recorded)} ({newest['checked_at'][:10]})"
            else:
                state = "unknown (never checked)"
            autos = ", ".join(f"`{a}`" for a in p.get("automations", [])) or "—"
            lines.append(f"| **{_md(p['name'])}** `{p['id']}` | {_md(p['purpose'])} | {p['lifecycle']} | {state} | {autos} |")
        lines.append("")
        for p in members:
            lines += _project_detail(p, projects)
    lines += _automation_table(records.automations, projects)
    lines += _dependency_table(records.projects, projects)
    return "\n".join(lines).rstrip() + "\n"


def _project_detail(p: dict, projects: dict[str, dict]) -> list[str]:
    out = [f"### {p['name']}", "", f"- **Path:** `{p['path']}` · **Class:** {p['classification']}"]
    repo = p.get("repo")
    if repo:
        visibility = f" ({repo['visibility']})" if repo.get("visibility") else ""
        out.append(f"- **Repository:** `{repo.get('path', p['path'])}` → {repo.get('remote') or 'no remote'}{visibility}")
    else:
        out.append("- **Repository:** none")
    if p.get("systems"):
        out.append("- **Systems:** " + "; ".join(f"{u['system']} ({', '.join(u.get('modes', []))})" for u in p["systems"]))
    if p.get("depends_on"):
        out.append("- **Depends on:** " + "; ".join(
            f"{projects[d['project']]['name']} — {d['kind']}: {d['detail']}" for d in p["depends_on"]))
    for label, key in (("Writes", "writes"), ("Skills", "skills")):
        if p.get(key):
            out.append(f"- **{label}:** " + "; ".join(p[key]))
    for label, key in (("Authority", "authority"), ("Recovery", "recovery"), ("Notes", "notes")):
        if p.get(key):
            out.append(f"- **{label}:** {p[key]}")
    out.append("")
    return out


def _automation_table(automations: list[dict], projects: dict[str, dict]) -> list[str]:
    if not automations:
        return []
    out = ["## Automations", "", "| Automation | Project | Cadence | Runs signed out | Browser | Enabled | Pause with |",
           "|---|---|---|---|---|---|---|"]
    yes_no = {True: "yes", False: "no", None: "unverified"}
    for a in sorted(automations, key=lambda a: (projects[a["project"]]["name"].lower(), a["id"])):
        out.append(
            f"| `{_md(a['id'])}` | {_md(projects[a['project']]['name'])} | {_md(a['cadence'])} | "
            f"{yes_no[a.get('runs_signed_out')]} | {a['needs_browser']} | {yes_no[a.get('enabled')]} | {_md(a['pause'])} |"
        )
    return out + [""]


def _dependency_table(project_list: list[dict], projects: dict[str, dict]) -> list[str]:
    rows = [(p, d) for p in project_list for d in p.get("depends_on", [])]
    if not rows:
        return []
    out = ["## Cross-project dependencies", "", "| From | To | Kind | Detail |", "|---|---|---|---|"]
    for p, d in rows:
        out.append(f"| {_md(p['name'])} | {_md(projects[d['project']]['name'])} | {d['kind']} | {_md(d['detail'])} |")
    return out + [""]


def render_status(records: Records, now: datetime) -> str:
    names: dict[str, str] = {"company": "Company"}
    for group, key in ((records.projects, "name"), (records.assets, "name"), (records.systems, "name"), (records.access, "service")):
        names.update({item["id"]: item[key] for item in group})
    names.update({a["id"]: a["id"] for a in records.automations})
    order = {s: i for i, s in enumerate(OBS_STATUSES)}
    lines = [f"Status as of {now.isoformat(timespec='minutes')}", ""]
    if not records.observations:
        lines.append("Nothing observed yet: every subject is unknown.")
    for obs in sorted(records.observations, key=lambda o: (order[effective_status(o, now)], names.get(o["subject"], o["subject"]))):
        status = effective_status(obs, now)
        hours = (now - parse_time(obs["checked_at"])).total_seconds() / 3600
        age = f"{hours:.0f}h" if hours < 48 else f"{hours / 24:.0f}d"
        stale = " (stale: treat as unknown)" if status == "unknown" and obs["status"] != "unknown" else ""
        lines.append(f"[{status.upper():9}] {names.get(obs['subject'], obs['subject'])}: {obs['statement']}  (checked {age} ago){stale}")
    open_items = sorted((i for i in records.queue if i["status"] in {"open", "in-progress", "waiting"}),
                        key=lambda i: (i["priority"], i.get("due") or "9999-12-31", i["id"]))
    lines += ["", f"Open work ({len(open_items)})", ""]
    for item in open_items:
        due = f" due {item['due']}" if item.get("due") else ""
        lines.append(f"{item['priority']} {item['kind']:11} {item['status']:11} [{item['owner']}] {item['title']}{due}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- operations


def append_history(ctx: Context, subject: str, summary: str, evidence: list[str] | None = None) -> None:
    row = {"at": now_local().isoformat(timespec="seconds"), "subject": subject, "summary": summary}
    if evidence:
        row["evidence"] = evidence
    with (ctx.root / "state" / "history.jsonl").open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def initialize(ctx: Context, company: str, timezone_name: str, workspace_root: str | None = None,
               projects_dir: str | None = None, functions: dict[str, str] | None = None,
               install_to: str | None = None, force: bool = False) -> list[str]:
    """Set this copy up for one company. Returns the files written."""
    cfg = ctx.config
    cfg["company"].update({"name": company, "timezone": timezone_name})
    if workspace_root:
        cfg["workspace"]["root"] = workspace_root
    if projects_dir:
        cfg["workspace"]["projects_dir"] = projects_dir
    if functions:
        cfg["functions"] = functions
    if install_to:
        cfg["instructions"]["install_to"] = install_to
    cfg.setdefault("template", {})["bootstrapped"] = True
    write_json(ctx.root / CONFIG_FILE, cfg)
    written = [CONFIG_FILE]

    values = {
        "company": company,
        "timezone": timezone_name,
        "ops": str(ctx.root),
        "workspace": str(ctx.workspace),
        "projects": str(ctx.workspace / ctx.projects_dir),
        "skills": ", ".join(f"`{s}`" for s in cfg.get("standing_skills", [])) or "none configured",
        "date": now_local().date().isoformat(),
    }
    for template, target in (("company-instructions.md", ctx.instructions_source), ("COMPANY.md", ctx.root / "COMPANY.md")):
        if target.exists() and not force:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(fill((ctx.root / "templates" / template).read_text(encoding="utf-8"), values),
                          encoding="utf-8", newline="\n")
        written.append(target.relative_to(ctx.root).as_posix())
    records = load_records(ctx)
    (ctx.root / "PROJECTS.md").write_text(render_projects(ctx, records), encoding="utf-8", newline="\n")
    written.append("PROJECTS.md")
    append_history(ctx, "company", f"Operations center initialized for {company} ({timezone_name}).", written)
    return written


def add_project(ctx: Context, project_id: str, name: str, function: str, purpose: str, path: str | None = None,
                classification: str = "business", lifecycle: str = "pilot", scaffold: bool = True) -> tuple[dict, list[str]]:
    """Register a new project and optionally create its folder with starter files.

    Raises ValueError, before anything is written, if the entry would make the registry invalid.
    """
    path = path or f"{ctx.projects_dir}/{name}"
    today = now_local().date().isoformat()
    entry = {
        "id": project_id, "name": name, "function": function, "classification": classification,
        "lifecycle": lifecycle, "purpose": purpose, "path": path, "repo": None, "systems": [],
        "depends_on": [], "automations": [], "writes": [],
        "authority": "Not written yet: record reads, writes and approvals in the project's CLAUDE.md.",
        "release": {"runs_from": "not deployed", "deploy_authority": "owner"},
        "recovery": "", "notes": f"Registered {today}.",
    }
    records = load_records(ctx)
    records.projects = records.projects + [entry]
    errors = [i for i in validate(ctx, records, check_paths=False, check_install=False) if i.level == "error"]
    if errors:
        raise ValueError("; ".join(f"{i.where}: {i.message}" for i in errors))

    created: list[str] = []
    if scaffold:
        folder = resolve_path(ctx, path)
        if not folder.exists():
            folder.mkdir(parents=True)
            created.append(str(folder))
        values = {"name": name, "id": project_id, "function": ctx.functions[function], "purpose": purpose,
                  "date": today, "company": ctx.company}
        for template, target in (("project-CLAUDE.md", "CLAUDE.md"), ("project.gitignore", ".gitignore")):
            destination = folder / target
            if destination.exists():
                continue  # never overwrite a project's own files
            text = (ctx.root / "templates" / template).read_text(encoding="utf-8")
            destination.write_text(fill(text, values), encoding="utf-8", newline="\n")
            created.append(str(destination))

    data = load_json(ctx.root / "registry" / "projects.json")
    data["projects"].append(entry)
    write_json(ctx.root / "registry" / "projects.json", data)
    append_history(ctx, project_id, f"Registered new project '{name}' ({function}).", created)
    return entry, created


def instructions_drift(ctx: Context) -> str | None:
    source, target = ctx.instructions_source, ctx.instructions_target
    if not source.exists():
        return f"company instructions missing: {source} (run: python tools/ops.py init)"
    if not target.exists():
        return f"not installed: {target} (run: python tools/ops.py install)"
    if target.read_bytes() != source.read_bytes():
        return f"{target} differs from {source.name} (run: python tools/ops.py install)"
    return None


def _normalize_remote(url: str) -> str:
    url = url.strip().lower().replace("git@github.com:", "https://github.com/")
    return url[:-4] if url.endswith(".git") else url.rstrip("/")


def origin_is_template(ctx: Context) -> bool:
    result = _git(ctx, "remote", "get-url", "origin")
    upstream = ctx.template_upstream
    return result.returncode == 0 and bool(upstream) and _normalize_remote(result.stdout) == _normalize_remote(upstream)


def _git(ctx: Context, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(ctx.root), *args], capture_output=True, text=True, encoding="utf-8")


# ---------------------------------------------------------------- commands


def cmd_init(ctx: Context, args: argparse.Namespace) -> int:
    functions = None
    if args.function:
        functions = {}
        for pair in args.function:
            key, _, title = pair.partition("=")
            if not ID_RE.match(key) or not title:
                print(f"--function must look like id=Title, got '{pair}'")
                return 1
            functions[key] = title
    for path in initialize(ctx, args.company, args.timezone, args.workspace_root, args.projects_dir,
                           functions, args.install_to, args.force):
        print(f"wrote {path}")
    print("next: BOOTSTRAP.md stage 4 (baseline survey)")
    return 0


def cmd_validate(ctx: Context, args: argparse.Namespace) -> int:
    issues = validate(ctx, load_records(ctx), check_paths=not args.no_paths)
    for issue in issues:
        print(issue)
    errors = sum(1 for i in issues if i.level == "error")
    print(f"{errors} error(s), {len(issues) - errors} warning(s)")
    return 1 if errors else 0


def cmd_render(ctx: Context, args: argparse.Namespace) -> int:
    target = ctx.root / "PROJECTS.md"
    text = render_projects(ctx, load_records(ctx))
    current = target.read_text(encoding="utf-8") if target.exists() else ""
    if args.check:
        print("PROJECTS.md is current" if current == text else "PROJECTS.md is out of date; run: python tools/ops.py render")
        return 0 if current == text else 1
    if current != text:
        target.write_text(text, encoding="utf-8", newline="\n")
        print("PROJECTS.md updated")
    else:
        print("PROJECTS.md already current")
    return 0


def cmd_status(ctx: Context, args: argparse.Namespace) -> int:
    sys.stdout.write(render_status(load_records(ctx), now_local()))
    return 0


def cmd_new_project(ctx: Context, args: argparse.Namespace) -> int:
    if args.function not in ctx.functions:
        print(f"unknown function '{args.function}'; choose from: {', '.join(ctx.functions)}")
        return 1
    try:
        entry, created = add_project(ctx, args.id, args.name, args.function, args.purpose, args.path,
                                     args.classification, args.lifecycle, scaffold=not args.no_scaffold)
    except ValueError as exc:
        print(f"not registered: {exc}")
        return 1
    for item in created:
        print(f"created {item}")
    print(f"registered {entry['id']} at {entry['path']}")
    cmd_render(ctx, argparse.Namespace(check=False))
    print("next: fill in the project's CLAUDE.md, then its registry entry (procedures/new-project.md)")
    return 0


def cmd_observe(ctx: Context, args: argparse.Namespace) -> int:
    path = ctx.root / "state" / "observations.json"
    data = load_json(path)
    entry = {
        "id": args.id, "subject": args.subject, "status": args.status, "statement": args.statement,
        "checked_at": now_local().isoformat(timespec="seconds"), "evidence": args.evidence,
        "ttl_hours": args.ttl_hours,
    }
    data["observations"] = sorted([o for o in data["observations"] if o["id"] != args.id] + [entry], key=lambda o: o["id"])
    records = load_records(ctx)
    records.observations = data["observations"]
    problems = [i for i in validate(ctx, records, check_paths=False, check_install=False)
                if i.level == "error" and i.where.startswith("observations/")]
    if problems:
        for issue in problems:
            print(issue)
        return 1
    write_json(path, data)
    append_history(ctx, args.subject, f"observed {args.id}: {args.status} — {args.statement}", args.evidence)
    print(f"recorded observation {args.id}")
    return 0


def cmd_record(ctx: Context, args: argparse.Namespace) -> int:
    append_history(ctx, args.subject, args.summary, args.evidence)
    print("recorded")
    return 0


def cmd_pause(ctx: Context, args: argparse.Namespace) -> int:
    automations = [a for a in load_records(ctx).automations if a["project"] == args.project]
    if not automations:
        print(f"no automations registered for project '{args.project}'")
        return 1
    verb = "RESUME" if args.resume else "PAUSE"
    failed = 0
    for a in automations:
        if a["kind"] != "windows-task" or not args.apply:
            step = a.get("resume", "reverse the pause step") if args.resume else a["pause"]
            label = "MANUAL" if a["kind"] != "windows-task" else f"WOULD {verb}"
            print(f"{label:13} {a['id']}: {step}")
            continue
        if os.name != "nt":
            print(f"{'SKIPPED':13} {a['id']}: Windows tasks can only be changed on Windows")
            failed += 1
            continue
        name = a["id"].split(":", 1)[1].replace("'", "''")
        find = f"$t = Get-ScheduledTask | Where-Object TaskName -eq '{name}' | Select-Object -First 1; if (-not $t) {{ exit 3 }}; "
        if args.resume:
            action = "Enable-ScheduledTask -TaskPath $t.TaskPath -TaskName $t.TaskName | Out-Null"
        else:
            action = ("if ($t.State -eq 'Running') { Stop-ScheduledTask -TaskPath $t.TaskPath -TaskName $t.TaskName }; "
                      "Disable-ScheduledTask -TaskPath $t.TaskPath -TaskName $t.TaskName | Out-Null")
        result = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", find + action],
                                capture_output=True, text=True)
        if result.returncode == 0:
            print(f"{verb + 'D':13} {a['id']}")
        else:
            reason = "no such task" if result.returncode == 3 else (result.stderr.strip().splitlines() or ["failed"])[-1]
            print(f"{'FAILED':13} {a['id']}: {reason} (tasks that run while signed out need an elevated shell)")
            failed += 1
    if not args.apply:
        print("nothing changed; add --apply to change Windows tasks")
    return 1 if failed else 0


def cmd_install(ctx: Context, args: argparse.Namespace) -> int:
    drift = instructions_drift(ctx)
    if args.check:
        print(drift or f"{ctx.instructions_target} is current")
        return 1 if drift else 0
    if drift is None:
        print(f"{ctx.instructions_target} already current")
        return 0
    if not ctx.instructions_source.exists():
        print(drift)
        return 1
    target = ctx.instructions_target
    if target.exists():
        backup = target.with_name(f"{target.name}.bak-{now_local().strftime('%Y%m%d-%H%M%S')}")
        backup.write_bytes(target.read_bytes())
        print(f"previous copy kept at {backup}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(ctx.instructions_source.read_bytes())
    print(f"installed {target}; sessions started from now on load it")
    return 0


def cmd_publish(ctx: Context, args: argparse.Namespace) -> int:
    if not ctx.bootstrapped:
        print("not published: this copy is not initialized for a company (run: python tools/ops.py init)")
        return 1
    if origin_is_template(ctx):
        print("not published: origin is the public template. Company records go to the company's own private "
              "repository (BOOTSTRAP.md, stage 2).")
        return 1
    errors = [i for i in validate(ctx, load_records(ctx)) if i.level == "error"]
    if errors:
        for issue in errors:
            print(issue)
        print("not published: fix the errors above")
        return 1
    cmd_render(ctx, argparse.Namespace(check=False))
    tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(ctx.root / "tests"),
                            "-t", str(ctx.root / "tests")], capture_output=True, text=True, encoding="utf-8")
    if tests.returncode != 0:
        print(tests.stderr[-2000:])
        print("not published: tests failed")
        return 1
    if not _git(ctx, "status", "--porcelain").stdout.strip():
        print("nothing to publish")
        return 0
    for step in (("add", "-A"), ("commit", "-q", "-m", args.message)):
        result = _git(ctx, *step)
        if result.returncode != 0:
            print(result.stdout + result.stderr)
            print(f"not published: git {step[0]} failed")
            return 1
    sha = _git(ctx, "rev-parse", "--short", "HEAD").stdout.strip()
    has_upstream = _git(ctx, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}").returncode == 0
    push = _git(ctx, "push", "-q") if has_upstream else _git(ctx, "push", "-q", "-u", "origin", "HEAD")
    if push.returncode != 0:
        print(push.stderr)
        print(f"committed {sha} locally; push failed")
        return 1
    print(f"published {sha}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="set this copy up for one company")
    p.add_argument("--company", required=True)
    p.add_argument("--timezone", required=True, help="IANA name, e.g. America/Chicago")
    p.add_argument("--workspace-root", help="company workspace folder (default: the parent of this repository)")
    p.add_argument("--projects-dir", help="project folder inside the workspace (default: Projects)")
    p.add_argument("--function", action="append", help="business function as id=Title; repeat to replace the defaults")
    p.add_argument("--install-to", help="where Claude Code loads the company instructions (default: ~/.claude/CLAUDE.md)")
    p.add_argument("--force", action="store_true", help="regenerate instructions/company.md and COMPANY.md from the templates")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("validate", help="check registry and state")
    p.add_argument("--no-paths", action="store_true", help="skip filesystem path checks")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("render", help="regenerate PROJECTS.md")
    p.add_argument("--check", action="store_true", help="exit 1 if PROJECTS.md is out of date")
    p.set_defaults(func=cmd_render)

    sub.add_parser("status", help="current observations and open work").set_defaults(func=cmd_status)

    p = sub.add_parser("new-project", help="register a project and create its starter folder")
    p.add_argument("--id", required=True, help="permanent id: lowercase letters, digits, hyphens")
    p.add_argument("--name", required=True, help="display name; also the folder name")
    p.add_argument("--function", required=True, help="a business function id from ops.config.json")
    p.add_argument("--purpose", required=True)
    p.add_argument("--path", help="folder relative to the workspace (default: <projects_dir>/<name>)")
    p.add_argument("--classification", default="business", choices=sorted(CLASSIFICATIONS))
    p.add_argument("--lifecycle", default="pilot", choices=sorted(LIFECYCLES))
    p.add_argument("--no-scaffold", action="store_true", help="register only")
    p.set_defaults(func=cmd_new_project)

    p = sub.add_parser("observe", help="add or replace one dated observation")
    p.add_argument("id")
    p.add_argument("--subject", required=True)
    p.add_argument("--status", required=True, choices=OBS_STATUSES)
    p.add_argument("--statement", required=True)
    p.add_argument("--evidence", action="append", required=True)
    p.add_argument("--ttl-hours", type=float, required=True, help="after this many hours the observation reads as unknown")
    p.set_defaults(func=cmd_observe)

    p = sub.add_parser("record", help="append one line to the operating history")
    p.add_argument("--subject", required=True)
    p.add_argument("--summary", required=True)
    p.add_argument("--evidence", action="append", default=[])
    p.set_defaults(func=cmd_record)

    p = sub.add_parser("pause", help="show or apply the pause steps for a project's automations")
    p.add_argument("--project", required=True)
    p.add_argument("--resume", action="store_true")
    p.add_argument("--apply", action="store_true", help="actually change Windows tasks (default: show the plan)")
    p.set_defaults(func=cmd_pause)

    p = sub.add_parser("install", help="install the company instructions where Claude Code loads them")
    p.add_argument("--check", action="store_true")
    p.set_defaults(func=cmd_install)

    p = sub.add_parser("publish", help="validate, render, test, commit and push the company records")
    p.add_argument("-m", "--message", required=True)
    p.set_defaults(func=cmd_publish)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    return args.func(load_context(), args)


if __name__ == "__main__":
    sys.exit(main())
