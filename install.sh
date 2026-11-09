#!/usr/bin/env bash
set -euo pipefail

SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
SKILL_TARGET="$HOME/.agents/skills/codex-quota-router"
AGENT_TARGET="$HOME/.codex/agents"
GLOBAL_AGENTS_FILE="$HOME/.codex/AGENTS.md"
SKIP_GLOBAL="${SKIP_GLOBAL_AUTO_ROUTING:-0}"

mkdir -p "$(dirname "$SKILL_TARGET")" "$AGENT_TARGET" "$HOME/.codex"
if [[ -d "$SKILL_TARGET" && "$(cd "$SKILL_TARGET" && pwd -P)" != "$SOURCE_ROOT" ]]; then
  cp -R "$SKILL_TARGET" "$SKILL_TARGET.backup.$(date +%Y%m%d%H%M%S)"
  rm -rf "$SKILL_TARGET"
fi
if [[ ! -d "$SKILL_TARGET" || "$(cd "$SKILL_TARGET" && pwd -P)" != "$SOURCE_ROOT" ]]; then
  cp -R "$SOURCE_ROOT" "$SKILL_TARGET"
fi
cp "$SOURCE_ROOT"/agents/*.toml "$AGENT_TARGET"/
rm -f "$AGENT_TARGET/terra-resolver.toml" "$AGENT_TARGET/terra-guard.toml"

if [[ "$SKIP_GLOBAL" != "1" ]]; then
  python3 - "$GLOBAL_AGENTS_FILE" "$SOURCE_ROOT/snippets/AGENTS.global.md" <<'PY2'
from pathlib import Path
import re, sys, shutil, datetime

target = Path(sys.argv[1])
block = Path(sys.argv[2]).read_text(encoding='utf-8').strip()
begin = '<!-- BEGIN CODEX_QUOTA_ROUTER -->'
end = '<!-- END CODEX_QUOTA_ROUTER -->'
existing = target.read_text(encoding='utf-8') if target.exists() else ''
if target.exists():
    stamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    shutil.copy2(target, target.with_name(target.name + '.backup.' + stamp))
pattern = re.compile(r'<!-- BEGIN CODEX_(?:LUNA_FIRST_ROUTER|QUOTA_ROUTER) -->.*?<!-- END CODEX_(?:LUNA_FIRST_ROUTER|QUOTA_ROUTER) -->', re.S)
if pattern.search(existing):
    updated = pattern.sub(block, existing)
else:
    updated = existing.rstrip() + ('\n\n' if existing.strip() else '') + block + '\n'
target.write_text(updated, encoding='utf-8')
PY2
fi

echo "Installed skill: $SKILL_TARGET"
echo "Installed custom agents: $AGENT_TARGET"
echo "Restart Codex if changes are not detected immediately."
