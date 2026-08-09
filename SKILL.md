---
name: codex-quota-router
description: Route Codex coding, debugging, review, refactor, testing, workflow, infrastructure, and codebase-analysis tasks to the cheapest viable GPT-5.6 agent. Default strongly to Luna, enforce real delegation when the parent model does not match, fall back to Terra when Luna is unavailable, and keep Sol rare. 自动为 Codex 开发任务选择并实际委派到 Luna、Terra、Sol；Luna 无法调用时自动升级 Terra。Do not use for casual Q&A or when the user explicitly pins a model.
---

# Codex Quota Router v1.3.0 (Quota-first)

Route work before broad exploration or edits. Optimize for **successful completion per credit**, not maximum theoretical quality.

## Non-negotiable policy

1. Honor an explicit user model or reasoning choice.
2. Otherwise prefer Luna. A task must earn an upgrade through risk, ambiguity, coupling, demonstrated reasoning failure, or Luna runtime unavailability.
3. **A route decision is not execution.** Printing `[路由] Luna High` does not satisfy this skill.
4. If the current parent does not exactly match the selected `model` and `model_reasoning_effort`, the parent **MUST delegate before substantive repository reads, edits, tests, or business scripts**. The parent may only do the minimal classification work needed to build the task packet.
5. After selecting a different model, the parent **MUST NOT continue the substantive task itself** unless the user explicitly disabled subagents/delegation.
6. Prefer the installed custom agent. If that agent profile is unavailable, explicitly spawn a subagent with the selected `model` and `model_reasoning_effort`.
7. If Luna cannot actually be invoked because the Luna model/runtime is unavailable, automatically fall back to **Terra Medium** for the same bounded task packet. Do not treat sandbox, filesystem permission, dependency, test, network-to-project-service, or other environment failures as Luna model unavailability.
8. Never choose `xhigh`, `max`, `ultra`, or Pro mode by default.
9. Use at most one worker subagent by default. A second read-only Luna helper is permitted only when its scope is independent, it materially reduces main-thread context, and the parent records why one worker cannot cover it.
10. Never run parallel write agents on overlapping files.
11. Do not scan the whole repository before routing. Use the request, repository instructions, `git status`, and at most three clearly relevant files to classify the task.

## Default budget profile

Use the **tight** profile unless the user says quality is more important than quota.

- Primary work: Luna Low / Medium / High.
- Terra: hard gates, hidden coupling, reasoning escalation, or **availability fallback when Luna cannot be invoked**.
- Sol: planning or diagnosis only for architecture-level or high-impact ambiguity; return implementation to Luna or Terra once bounded.
- Maximum attempts: two bounded attempts on the same task packet before escalation or stopping to report the blocker.

## Routing workflow

### 1. Check explicit overrides

If the user names a model, effort, budget mode, or says not to delegate, obey it. Do not silently override.

If the user says "不要子 Agent" or equivalent, this skill can only recommend a route; it cannot switch the already-running parent model. In that special case label the result as **recommended route**, never as executed model.

### 2. Classify with minimal context

Score the task using `references/routing-policy.md`:

- clarity: 0-2
- scope: 0-3
- coupling: 0-3
- risk: 0-4
- novelty: 0-2
- failed focused attempts: 0-2

Use `scripts/route_score.py` when the route is borderline or when an auditable recommendation is useful. Do not run the script if the route is obvious.

### 3. Apply hard gates

Hard gates override the numeric score:

- **Luna allowed by default:** ordinary UI work, APIs with established patterns, tests, docs, configuration, log analysis, bounded refactors, workflow/YAML changes, and known bug fixes.
- **Terra Medium minimum:** cross-module behavior with unclear ownership, cache/idempotency bugs, transaction boundaries, intermittent failures, or one failed focused Luna High attempt.
- **Terra High minimum:** schema/data migration, authentication/authorization, payments, destructive operations, production incident repair, concurrency/race conditions, rollback design, or changes with plausible data loss.
- **Sol Medium planning/diagnosis only:** architecture selection, multi-system redesign, unexplained failures after a competent Terra attempt, or a high-impact decision with several plausible approaches and no safe local fix.

Do not use Sol merely because there are many files. Large but repetitive work belongs to Luna.

### 4. Select the cheapest viable route

| Route | Default use |
|---|---|
| `luna_fast` — Luna Low | Text, names, styles, config values, targeted searches, tiny deterministic edits |
| `luna_worker` — Luna Medium | Default implementation, 1-5 files, clear acceptance criteria, normal tests |
| `luna_deep` — Luna High | Bounded multi-file changes, ordinary frontend/backend integration, nontrivial debugging, careful review |
| `terra_resolver` — Terra Medium | Hidden coupling, cache/idempotency, intermittent behavior, unclear cross-module ownership; also Luna availability fallback |
| `terra_guard` — Terra High | Data/auth/concurrency/production-risk work, migration and rollback validation |
| `sol_architect` — Sol Medium | Read-only architecture or root-cause plan; not routine implementation |

### 5. Build a bounded task packet

Before spawning, give the worker:

- exact goal;
- known target files or search boundary;
- constraints and prohibited changes;
- acceptance criteria;
- required validation commands;
- requested return format: changed files, checks run, remaining risks.

Do not send a vague instruction such as “fix the project.”

### 6. Mandatory dispatch contract

Read `references/execution-contract.md` and follow it literally.

For the selected route, use the pure compatibility decision from `route_score.py`: the parent may set `parent_reused=true` only when its model matches and its effort is **at least** the target effort. Thus Luna High may reuse a Luna Medium/Low target, while Luna Medium cannot reuse a Luna High target; cross-model work remains delegated.

- If `parent_reused=true` and isolation adds no value: execute directly.
- If parent does not match: **dispatch is mandatory**. Do not continue implementation in the parent.

Dispatch order:

1. Invoke the installed custom agent matching the route (`luna_fast`, `luna_worker`, `luna_deep`, `terra_resolver`, `terra_guard`, or `sol_architect`).
2. If the custom agent profile itself is missing/unregistered, explicitly spawn a native subagent with the exact selected model and effort.
3. If the selected route is Luna and the Luna model/runtime cannot be invoked, reuse the identical bounded task packet and dispatch `terra_resolver` (`gpt-5.6-terra`, `medium`).
4. If Terra availability fallback also cannot be invoked, stop and report the execution blocker. Do not silently resume in the mismatched parent.

Suggested direct settings:

- Luna Low: `gpt-5.6-luna`, `low`
- Luna Medium: `gpt-5.6-luna`, `medium`
- Luna High: `gpt-5.6-luna`, `high`
- Terra Medium: `gpt-5.6-terra`, `medium`
- Terra High: `gpt-5.6-terra`, `high`
- Sol Medium: `gpt-5.6-sol`, `medium`

The parent remains responsible for task-packet construction, integration, conflict resolution, and final verification, but must not impersonate the selected worker.

### 7. Runtime verification and truthful status

Treat these as distinct states:

1. `route_decided` — recommendation only.
2. `dispatch_requested` — selected agent/model was requested.
3. `worker_started` — a separate worker/subagent exists.
4. `effective_model_verified` — runtime/session evidence confirms actual model and effort.
5. `worker_completed` — delegated task completed.

`worker_completed` requires a worker result nonce or concrete business result. It does **not** require runtime model metadata: if the worker returned successfully but its effective model is unavailable, record `worker_completed` plus `metadata_unverified`, never `start_unknown`.

**Never describe a route as “Luna 已执行” merely because the route was Luna.**

- Before dispatch: `[路由建议] Luna High｜原因：...`
- After a worker is created but effective runtime metadata is not available: `[执行请求] Luna High｜worker=luna_deep｜实际模型待核验`
- Only after runtime/session evidence confirms it: `[实际执行] Luna High｜effective_model=gpt-5.6-luna｜effort=high`
- On availability fallback: `[回退执行] Terra Medium｜原因：Luna runtime unavailable`

If runtime metadata is not accessible from the current environment, say it is unverified rather than inferring it from the agent TOML.

### 8. Retry, availability fallback, and reasoning escalation

Keep **availability fallback** separate from **reasoning escalation**.

#### Luna availability fallback -> Terra Medium

Trigger only when the execution mechanism returns evidence that Luna itself cannot be invoked, for example:

- model unavailable / unsupported / not allowed;
- Luna-specific capacity or quota rejection;
- registered Luna profile resolves to no usable Luna worker and explicit Luna spawn also fails.

Do **not** trigger availability fallback for:

- sandbox initialization failure;
- filesystem permission/locked handle;
- missing dependency;
- test failure;
- project service/network failure;
- malformed task input;
- unrelated pre-existing failure.

For Luna availability fallback, do not rescore the task. Reuse the same packet and use `terra_resolver` / Terra Medium unless an existing hard gate already required Terra High. TLS/transport failures stop for inspection; they never authorize Terra fallback.

#### Reasoning escalation ladder

1. Luna Low -> Luna Medium when the task requires real reasoning.
2. Luna Medium -> Luna High after one focused reasoning failure.
3. Luna High -> Terra Medium only when failure shows hidden coupling, ambiguity, or incorrect repeated reasoning.
4. Terra Medium -> Terra High for newly discovered risk or deep cross-module behavior.
5. Terra High -> Sol Medium planning only when the issue is architecture-level or still lacks a coherent root cause.

After Terra or Sol produces a bounded plan, downgrade implementation to Luna High whenever Luna is available and the plan isolates files, invariants, and tests.

### 9. Verification

Verification should usually stay on Luna when Luna is available:

- targeted tests and formatting: Luna Low or Medium;
- reviewing ordinary diffs: Luna Medium;
- reviewing complex behavioral diffs: Luna High;
- security, data integrity, migration, or concurrency review: Terra High.

Do not add a second expensive reviewer unless the risk gate requires it.

When a worker already ran the exact same validation command and returned its concrete result, record `verification_reused=true` and do not repeat it in the parent. A normal business task may be the half-open probe; do not create a default health-only worker merely to test Luna.

### Quota-first controller and audit

Call `model_availability.py decide` before a Luna dispatch. Its `dispatch_action` is authoritative: `use_luna`, `probe_luna`, `use_fallback`, or `inspect_existing_probe`. A live probe is inspected, not replaced with Terra. The half-open lease is 300 seconds; stale leases are reclaimable. Inconclusive, transport, and metadata-unverified outcomes must release the lease to `closed/unknown`.

Do not manually close the circuit. Only a successful worker/probe result may record `available`; an explicit Luna availability rejection may record `unavailable`. Audit each dispatch with parent/route/requested/effective model fields and `parent_reused`, `worker_count`, `fallback_count`, `probe_count`, `verification_reused`, and `reasoning_escalation_count`. These are event counts, not real credit measurements.

## User-visible routing note

At the start of substantive work, show one compact line only. Until dispatch occurs, use **recommendation wording**:

`[路由建议] Luna High｜原因：边界明确的多文件改动｜升级条件：出现跨模块语义、连续推理失败或 Luna 无法调用`

Do not display `[实际执行]` until runtime evidence supports it.

For trivial tasks, route silently. Do not turn routing into a long report unless the user asks.

## Stop conditions

Stop and report instead of burning quota when:

- required files, credentials, services, or reproducible inputs are missing;
- two bounded attempts fail for the same external reason;
- success requires a destructive action not authorized by the user;
- Terra fallback cannot access a worker after Luna availability fallback;
- the only remaining option would be silently continuing the task in a parent whose model/effort does not match the selected route.

## Supporting files

- `references/routing-policy.md`: scoring and hard gates.
- `references/execution-contract.md`: mandatory dispatch, runtime verification, and Luna -> Terra fallback contract.
- `references/scenarios.md`: representative task routes.
- `references/task-packet.md`: delegation template.
- `scripts/route_score.py`: deterministic score and availability-fallback helper.
- `scripts/model_availability.py`: persistent CLOSED/OPEN/HALF_OPEN controller and dispatch audit. Call it before every Luna dispatch; this Skill cannot intercept runtimes that skip the controller.
- `references/availability-contract.md`: controller commands, audit IDs, and `start_rejected` versus `start_unknown` rules.
- `agents/*.toml`: optional custom agents copied by the installer.
