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
    "v1.3.0 (Quota-first)",
    "A route decision is not execution",
    "MUST delegate before substantive repository reads",
    "Luna cannot actually be invoked",
    "effective_model_verified",
    "start_unknown",
    "availability-contract.md",
):
    if required_phrase not in text:
        errors.append(f"SKILL.md missing execution invariant: {required_phrase}")

required = [
    "references/routing-policy.md",
    "references/execution-contract.md",
    "references/availability-contract.md",
    "references/scenarios.md",
    "references/task-packet.md",
    "scripts/route_score.py",
    "scripts/model_availability.py",
    "scripts/run_tests.py",
    "tests/test_model_availability.py",
    "snippets/AGENTS.global.md",
    "agents/luna-fast.toml",
    "agents/luna-worker.toml",
    "agents/luna-deep.toml",
    "agents/terra-resolver.toml",
    "agents/terra-guard.toml",
    "agents/sol-architect.toml",
]
for rel in required:
    if not (root / rel).is_file():
        errors.append(f"missing {rel}")

if (root / "VERSION").read_text(encoding="utf-8").strip() != "1.3.0":
    errors.append("VERSION must be 1.3.0")

if tomllib:
    try:
        config = tomllib.loads((root / "snippets" / "config.toml").read_text(encoding="utf-8"))
        if config.get("agents", {}).get("max_concurrent_threads_per_session") != 1:
            errors.append("snippets/config.toml must default max_concurrent_threads_per_session to 1")
    except Exception as exc:
        errors.append(f"invalid snippets/config.toml: {exc}")

if tomllib:
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

if errors:
    print("VALIDATION FAILED")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)

print("VALIDATION PASSED")
print(f"Skill root: {root}")
print(f"Agent profiles: {len(list((root / 'agents').glob('*.toml')))}")
