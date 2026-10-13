#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import tomllib
except ImportError:  # pragma: no cover
    tomllib = None

root = Path(__file__).resolve().parents[1]
errors: list[str] = []

skill = root / "SKILL.md"
text = skill.read_text(encoding="utf-8")
match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
if not match:
    errors.append("SKILL.md is missing YAML frontmatter")
else:
    front = match.group(1)
    if not re.search(r"^name:\s*codex-quota-router\s*$", front, re.M):
        errors.append("frontmatter name is invalid")
    if not re.search(r"^description:\s*.+$", front, re.M):
        errors.append("frontmatter description is missing")

for required_phrase in (
    "Codex Quota Router 1.4.2-local",
    "Recommended routes are not proof of execution",
    "Lightweight reuse is opt-in",
    "runtime evidence",
    "execution failure is a blocker",
):
    if required_phrase.lower() not in text.lower():
        errors.append(f"SKILL.md missing execution invariant: {required_phrase}")

required = [
    "references/routing-policy.md",
    "references/execution-contract.md",
    "references/scenarios.md",
    "references/task-packet.md",
    "scripts/route_score.py",
    "scripts/run_tests.py",
    "tests/test_route_score.py",
    "snippets/AGENTS.global.md",
    "agents/luna-fast.toml",
    "agents/luna-worker.toml",
    "agents/luna-deep.toml",
    "agents/sol-resolver.toml",
    "agents/sol-guard.toml",
    "agents/sol-architect.toml",
]
for rel in required:
    if not (root / rel).is_file():
        errors.append(f"missing {rel}")

active_files = [
    skill,
    root / "references" / "routing-policy.md",
    root / "references" / "execution-contract.md",
    root / "references" / "scenarios.md",
    root / "README.md",
    root / "README_EN.md",
    root / "snippets" / "AGENTS.global.md",
    root / "scripts" / "route_score.py",
    root / "scripts" / "run_tests.py",
]
active_text = "\n".join(path.read_text(encoding="utf-8") for path in active_files if path.is_file()).lower()
for obsolete in ("model_availability.py", "--luna-unavailable", "--luna-available", "probe_luna", "start_unknown", "use_fallback"):
    if obsolete in active_text:
        errors.append(f"active router references retired availability policy: {obsolete}")

if (root / "VERSION").read_text(encoding="utf-8").strip() != "1.4.2-local":
    errors.append("VERSION must be 1.4.2-local")

if tomllib:
    try:
        config = tomllib.loads((root / "snippets" / "config.toml").read_text(encoding="utf-8"))
        if "max_concurrent_threads_per_session" in config.get("agents", {}):
            errors.append("snippets/config.toml must not impose a worker-count cap")
    except Exception as exc:
        errors.append(f"invalid snippets/config.toml: {exc}")

if tomllib:
    expected_models = {
        "luna-fast.toml": ("gpt-6-luna", "low"),
        "luna-worker.toml": ("gpt-6-luna", "medium"),
        "luna-deep.toml": ("gpt-6-luna", "high"),
        "sol-resolver.toml": ("gpt-6.1-sol", "medium"),
        "sol-guard.toml": ("gpt-6.1-sol", "high"),
        "sol-architect.toml": ("gpt-6-astra", "medium"),
    }
    for path in sorted((root / "agents").glob("*.toml")):
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"invalid TOML {path.name}: {exc}")
            continue
        for field in ("name", "description", "developer_instructions", "model", "model_reasoning_effort"):
            if not data.get(field):
                errors.append(f"{path.name} missing {field}")
        if data.get("model_reasoning_effort") in {"xhigh", "max", "ultra"}:
            errors.append(f"{path.name} violates tight budget effort policy")
        if (data.get("model"), data.get("model_reasoning_effort")) != expected_models.get(path.name):
            errors.append(f"{path.name} does not match the GPT-6 routing profile")

if errors:
    print("VALIDATION FAILED")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)

print("VALIDATION PASSED")
print(f"Skill root: {root}")
print(f"Agent profiles: {len(list((root / 'agents').glob('*.toml')))}")
