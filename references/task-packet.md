# Bounded task packet template

Use this template when delegating.

```text
Requested route:
- agent: <luna_fast | luna_worker | luna_deep | terra_resolver | terra_guard | sol_architect>
- model: <exact model id>
- reasoning effort: <low | medium | high>

Goal:
<one concrete outcome>

Scope:
- Allowed files/directories: <paths or narrow search boundary>
- Do not change: <explicit exclusions>

Known context:
- <relevant behavior, error, prior decision>

Acceptance criteria:
1. <observable result>
2. <observable result>

Validation:
- <commands/tests>

Return:
- Worker/agent identity
- Requested model + effort
- Effective model + effort if runtime evidence is accessible; otherwise explicitly say unverified
- Summary of root cause or implementation
- Files changed
- Validation results
- Remaining risks/blockers
```

Rules:

- Keep one owner for overlapping writes.
- Ask the worker to stop if scope must expand materially.
- Do not paste whole repositories or huge logs into the parent thread.
- Prefer exact file references and concise evidence.
