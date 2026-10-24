---
type: report
title: The four-framework experiment, complete account
description: One-document account of the Inspect AI versus Ragas, DeepEval, and MLflow coding-repair comparison, from the motivating question through measured results, teaching materials, and framework conclusions.
timestamp: "2026-10-24T09:59:22-04:00"
---

# The four-framework experiment, complete account

This is the single consolidated account of everything done in this repository: why the experiment exists, how it was designed and built, what it measured, what was built afterward to teach it, and what the long discussions concluded. Specialized documents carry the detail for each area — [results](comparison-results.md), [runbook](comparison-runbook.md), [tutorial](inspect-ai-tutorial.md), [presentation](inspect-ai-presentation.md), [review and plan](inspect-ai-review.md) — and each links back here.

## At a glance

- **Question.** *Isn't Inspect AI just fancy telemetry storage with a presentation layer? Can't Ragas, DeepEval, or MLflow do the same?*
- **Method.** Run one identical coding-repair agent experiment through all four frameworks, twice: once grading shared saved trajectories, once letting each framework run the whole experiment natively — plus a deterministic interrupted-run recovery test.
- **Headline result.** All four frameworks returned identical grades for identical work. Inspect's measured advantages were integrated sandbox execution and reuse of already-completed tasks after an interruption — not better grading.
- **Cost.** The recorded OpenAI demo cost about one cent of tokens. Controls, scoring, and recovery made no model calls.
- **Dates.** Conceived, built, run, and documented on 2026-10-04; made portable (DeepSeek, Windows) on 2026-10-11; turned into teaching material and interrogated on 2026-10-18.

## Timeline

| Date | What happened | Artifacts |
| --- | --- | --- |
| 2026-10-04 (morning) | Repository created with two uploaded Inspect AI examples. | `Inspect_Eg_1/`, `Inpect Eg_2/` |
| 2026-10-04 | Conversation questioning Inspect's value; review of both examples; upstream Inspect source snapshotted as reference; comparison proposed. | [`inspect-ai-conversation.md`](../inspect-ai-conversation.md), [review](inspect-ai-review.md), [`reference/inspect_ai/`](../reference-snapshots.md) |
| 2026-10-04 | The comparison implemented, executed, and documented the same day. | [`comparison/`](../comparison/), [results](comparison-results.md), [runbook](comparison-runbook.md), [`comparison/runs/2026-10-04-demo/`](../comparison/runs/2026-10-04-demo/summary.json) |
| 2026-10-04 | Explanation sessions unpacking the review and what the experiment proves. | `session-transcripts/10-04-2026/` |
| 2026-10-11 | README written; DeepSeek provider support and Windows compatibility added; Inspect's role in the comparison documented. | [`README.md`](../README.md), `comparison/` updates |
| 2026-10-18 | Teaching arc: demo walkthrough, simple tutorial, rejected mock, real Docker repair tutorial with a recorded run, nine-slide presentation. | [tutorial](inspect-ai-tutorial.md), [`tutorial/`](../tutorial/), [presentation](inspect-ai-presentation.md), [slides](inspect-ai-slides.html) |
| 2026-10-18 | Discussions on what Inspect offers, its primitives, and how it relates to the other frameworks. | `session-transcripts/10-18-2026/` |

## 1. The question that started it

The project began with the user's challenge, preserved verbatim in the [original conversation](../inspect-ai-conversation.md):

> isn't inspect ai just a fancy storage of telemetry and presentation layer. cant the other software such ragas or DeepEval do same? What about ml flow?

The conversation's answer set the terms for everything after it: the frameworks overlap heavily, but Inspect's core is an **evaluation runner**, not a storage or display layer. For simple question answering, a small model-calling script with Ragas or DeepEval scoring and MLflow tracking is enough. Inspect becomes compelling when the framework must own the evaluation procedure — especially agent benchmarks with tools and environments. The practical question is not *can the others produce the same score or dashboard* but **how much execution infrastructure you must build and maintain yourself**. That claim deserved a test, not an assumption, and the test became this experiment.

## 2. Starting material and the review

The repository opened with two Inspect examples:

- **`Inspect_Eg_1/`** — a three-question DeepSeek evaluation (`chain_of_thought()` solver, `match()` scorer) run through the OpenAI-compatible provider. Saved log: 2 of 3 correct. The failed question asked for a data structure for vector search and targeted `vector database`; the model answered `HNSW graph` — a defensible answer, exposing a target/scoring problem rather than a knowledge gap. Inspect's `match()` defaults to matching at the *end* of the response, which mattered for interpreting that score. This file also contained a hardcoded DeepSeek API key, tracked by Git (see [gaps](#11-known-gaps-and-open-threads)).
- **`Inpect Eg_2/`** — a third-party tutorial ("test-an-llm-with-inspect-ai", Arun Godwin Patel, 2025-08-21, `inspect_ai==0.3.114`) with seven tasks: exact match, GSM8K few-shot, HellaSwag multiple choice, theory of mind with self-critique, model-graded security Q&A, MATH-500 with a custom equivalence scorer, and a custom addition tool. Saved logs covered three tasks; a hello-world re-run with DeepSeek was added by this project.

The [review](inspect-ai-review.md) concluded both examples **mostly demonstrate question answering**, not sandboxed agent tasks — so they could not show Inspect's distinctive capability. It also flagged scorer defects (the mathematics grader's stray `xw` template bug, the tool example scoring only the final number). The proposed next step was exactly the experiment that was then built: give an agent a broken Python project in Docker, let it inspect, edit, and run commands, then grade the resulting project with fixed tests.

## 3. Designing a fair comparison

The experiment holds everything constant except the framework wiring. A cooperative coding-repair agent receives a small broken Python function, a shell tool, and a fixed budget, and must produce a corrected `/workspace/project.py`:

| Task | Requirement |
| --- | --- |
| `slug` | Lowercase ASCII, keep digits, collapse other runs to one hyphen, strip ends, empty → empty. |
| `intervals` | Merge overlapping/touching pairs, sorted, no mutation of input or nested pairs. |
| `chunks` | Successive slices including final short slice, empty → `[]`, `ValueError` for `size <= 0`. |

Grading always runs **after** the agent finishes, in a **separate container** with fixed tests injected — the agent can never edit the tests, and generated code never runs on the host. Every live run used the same requirements, starting source, system prompt, model, tool permissions, and call budget (`gpt-4o-mini-2024-07-18`, temperature 0, at most six model calls and 700 output tokens per case).

Three evaluation passes separate the questions the experiment can actually answer:

1. **Shared trajectories (no per-framework model behavior).** One application agent produced the three final projects; every framework then graded those exact same saved projects through its own custom executable scorer, with six extra controls (broken code must fail, references must pass).
2. **Live runs (each framework owns the experiment).** Inspect used its native dataset, solver generation, tool dispatch, Docker sandbox, scorer, and evaluation-set runner; Ragas used `@experiment` with a custom `discrete_metric`; DeepEval its traced dataset iterator with a custom `BaseMetric`; MLflow `genai.evaluate(predict_fn=...)` with a custom code-based scorer. The last three all called the same application agent and the same custom Docker workspace code.
3. **Recovery (no model calls).** A deterministic fixture completes one repair callback, blocks during the next, is interrupted (SIGINT, escalating to SIGKILL after 30 s), and the same native runner is rerun against the same storage — measuring **reuse of already-completed tasks**, not mid-conversation checkpoint restoration.

## 4. Building it

Everything lives in [`comparison/`](../comparison/): `run.py` (CLI orchestrator), `worker.py` (one subprocess per framework so tracing hooks and event-loop changes cannot leak across), `agent.py` (the shared OpenAI application agent), `cases.py` (tasks and budget), `sandbox.py` (Docker workspace and the fixed-test grader shared by all four), four adapters, `recovery.py`, and five unit tests. Pinned SDKs: inspect-ai 0.3.276, ragas 0.4.3, deepeval 4.2.8, mlflow 3.16.1, openai 3.3.0, langchain-community 0.3.31 (pinned for Ragas compatibility). Docker ran in a dedicated Colima VM profile with the global context restored afterward; agent containers have no network, no host mounts, a read-only root filesystem, tmpfs workspaces, and no credentials.

Integration problems encountered and fixed — each part of the measured engineering cost:

- Ragas's loose dependency range selected langchain-community 0.4.2, which removed a module Ragas imports; pinning 0.3.31 restored it.
- Calling Ragas's synchronous `score()` from the async callback triggered an event-loop error; `ascore()` resolved it.
- The MLflow adapter initially used an older result-table name; 3.16.1 exposes `result_df` with a `response` record column.
- MLflow's prediction-trace validation invokes the application one extra time; the adapter skips it (the callback is explicitly traced) and verifies stored traces afterward.
- **Inspect's own live-run defect:** its Docker file-copy reader could not read the tmpfs workspace (shell reads worked). The adapter now extracts source through sandbox execution. The failed first attempt and its token usage are preserved in `comparison/runs/2026-10-04-demo/setup-failures/`, and the report accounts for it separately rather than hiding it — the framework whose advantage is integrated execution was also the one that hit an execution bug first.

## 5. Measured results

### Pass one — the same saved projects

Every framework returned: slug **pass**, intervals **fail**, chunks **pass**; all three broken controls failed; all three references passed. The interval repair sorted the outer list but kept a reference to an original nested pair, so merging mutated the caller's input — the scorer caught it despite the agent's claim to the contrary. Identical inputs to the same deterministic grader gave identical grades; this verifies the adapters and result recording, not judge quality.

### Pass two — each framework runs the experiment

| Framework | Slug | Intervals | Chunks | Passed | Input tokens | Output tokens |
| --- | --- | --- | --- | --- | ---: | ---: |
| Inspect | Pass | Fail | Pass | 2 of 3 | 7,951 | 740 |
| Ragas | Fail | Fail | Pass | 1 of 3 | 8,095 | 789 |
| DeepEval | Pass | Fail | Pass | 2 of 3 | 7,919 | 754 |
| MLflow | Pass | Fail | Pass | 2 of 3 | 7,919 | 765 |

Each setup made 18 model calls, spending the full six-call allowance per task. Ragas's slug attempt produced invalid Python after shell-quoting errors. Every run failed the intervals mutation requirement. These are separate generations; temperature zero does not guarantee identical outputs, and SDK serialization differs — Ragas's lower score is **not** a framework defect.

### Recovery after interruption

| Framework | Callbacks invoked after restart | Already-completed callback repeated? |
| --- | --- | --- |
| Inspect | Intervals only | No |
| Ragas | Intervals and slug | Yes, intervals |
| DeepEval | Slug and intervals | Yes, slug |
| MLflow | Slug and intervals | Yes, slug |

Inspect's `eval_set()` reused the completed slug task and scheduled only the missing one; the others re-invoked a completed callback in the tested configuration (which does not prove they *cannot* resume with extra work).

### Cost and checks

Total model usage ≈ **$0.0099** (common-agent ~$0.0016, live phases ~$0.0066, failed Inspect setup attempt ~$0.0017, preflight ~$0.000003), computed from token counts against published GPT-4o-mini prices in [`costs.json`](../comparison/runs/2026-10-04-demo/costs.json). All five automated tests passed (budget enforcement, grading controls, invalid-Python rejection, sandbox isolation, cleanup); no generated code ran on the host; [`verification.json`](../comparison/runs/2026-10-04-demo/verification.json) records the evidence.

## 6. What it showed

- **Inspect's advantage is integrated execution and completed-work reuse — not better grading.** All four frameworks graded identical projects identically through the same fixed tests.
- **The recovery difference was the clearest measured win:** after interruption, only Inspect resumed without repeating finished work.
- **MLflow's tracing was particularly useful** — three agent traces, six model-call child spans each, 21 spans total, verified after the run.
- **What each framework supplied:** Inspect provided the model/tool loop, starting-file injection, Docker provisioning, and completion tracking; the application still supplied a shell-tool wrapper, the fixed-test scorer, and a bounded solver to match the shared budget. Ragas, DeepEval, and MLflow each scheduled, scored, and recorded — over the application's own agent, workspace, and tool loop.
- **Recommendation, as recorded:** choose Inspect when the evaluation must create environments, expose tools, grade actions or final files, and resume a collection of agent tasks. If an application already owns its agent loop and environments, the others can evaluate it without handing execution to Inspect, and there is no reason to replace a working evaluation stack merely for a different score viewer.

The explanation sessions distilled the mechanism into one phrase the project kept reusing: **integrated execution** — one managed run that provisions the environment, routes the agent's tools into it, drives the multi-turn loop under limits, invokes grading, and records conversation, actions, and score together. The alternative is wiring agent runner, container system, grader, and logger yourself and maintaining the seams — exactly where bugs distort results (grading the wrong files, carrying changes between attempts, recording failures without enough evidence). Inspect is an evaluation runner, not a sandboxing engine (Docker supplies the isolation) and not a better judge; it can faithfully run a badly designed test, so the task and the success criteria remain yours.

## 7. Portability (2026-10-11)

The comparison was made runnable on this team's actual setup: DeepSeek through the OpenAI-compatible provider (`deepseek-flash` by default, overridable in `comparison/cases.py`), Windows compatibility (Docker Desktop named-pipe `DOCKER_HOST`, `PYTHONUTF8` for a rich/cp1252 crash, antivirus quarantine workaround, POSIX/Windows kill paths in recovery), a 418-line README with setup, environment, troubleshooting, and cost sections, and a section documenting Inspect's exact role with its primitive-to-code mapping.

## 8. Teaching arc (2026-10-18)

The user's goal shifted to *teaching* Inspect AI. The session established the six-step pedagogical order the materials now follow:

1. Define one repair problem as a dataset sample.
2. Create an Inspect `Task`.
3. Configure the solver and shell tool.
4. Run the agent inside a Docker sandbox.
5. Score the repair with fixed tests.
6. Open the evaluation log and explain what happened.

A first simple tutorial (three-question `capitals` eval in `tutorial/first_eval.py`, smoke-tested with `mockllm/model`, then run live with DeepSeek — all three questions passed) was rejected as insufficient: *"prepare an actual tutorial then, dont just fake/mock."* The response was the real six-step tutorial: one broken `sum_even()` function, a real DeepSeek agent, a two-container Docker sandbox (`default` agent workspace + isolated `grader`), five fixed unit tests injected only into the grader, and a checked-in recorded run ([`tutorial/recorded/`](../tutorial/recorded/), 2026-10-18, four generations, four shell calls, accuracy 1.0) with control evidence (broken source fails 4 of 5 tests; reference repair passes 5 of 5). The [presentation script](inspect-ai-presentation.md) and [nine-slide deck](inspect-ai-slides.html) wrap the same run for a live audience, with exact terminal commands, narration for both successful and failed live runs, and a clearly labeled recorded-run fallback — plus explicit "do not claim" guardrails (not a hardened grader, not checkpoint restoration, not general coding ability).

## 9. The framework conclusions (2026-10-18 discussions)

**What Inspect offered here:** it did not make the repair smarter — it supplied the agent loop (send, execute tools, return outputs), sandbox management (start containers, seed the broken file, clean up), evaluation execution (connect problems to solver and scorer, enforce limits, compute metrics), and an inspectable record (messages, tool calls, outputs, repaired source, test results, token usage). For one function a Python script would be enough; Inspect pays off when evaluating many problems or comparing models repeatedly without rebuilding that machinery. Presentation line: *"We're demonstrating a repeatable, inspectable evaluation of an agent, not just watching an AI fix code."*

**Versus the other frameworks:** the distinction is integrated execution of sandboxed agent experiments, not better scoring — less execution machinery to build, reuse after interruption, no grading advantage. *"Other frameworks evaluated the agent we built. Inspect supplied more of the machinery needed to run the experiment itself."*

**Its composable primitives** (all exercised by the tutorial): `Sample`/dataset (requirements + broken file), `Solver` (composed `system_message()` + `use_tools()` + `generate()`), `Tool` (built-in `bash()`, custom via `@tool`), `SandboxEnvironment` (separate Docker sandboxes for agent and grader), `Scorer`/`Score` (`repair_tests()` returning repaired source and test output), `Metric` (`accuracy()`), `Task` (wiring plus limits) — run by `eval()`/`eval_set()`. "Composable" means the parts change independently: swap the solver, the tool, or the model without rewriting the runner.

**Complementarity, after deliberate reconsideration:** yes, Inspect can complement Ragas, DeepEval, and MLflow — but they are *not* four mandatory layers with exclusive responsibilities; all four overlap (Inspect scores and tracks; Ragas and DeepEval run evaluations; MLflow evaluates, not just tracks). The useful question is *which framework owns execution, and which existing capabilities do you want to reuse?* A combined architecture (Inspect runs the agent; a Ragas/DeepEval metric wrapped as a custom scorer; results logged to MLflow) is possible but requires integration code — and this experiment compared separate execution setups, never an integrated pipeline. For the repair tutorial, Inspect plus Python tests is already sufficient.

**Environment snapshots vs checkpointing — the corrected answer:** Inspect provides *repeatable starting environments* (fresh sandboxes from a defined image and configuration every run) and, when enabled with a compatible agent, *checkpoint and resume* (agent state plus selected sandbox files restored into a fresh container). That is not a full running-machine snapshot: process memory, running commands, and external services are not restored, and loading is not instantaneous.

## 10. Where everything lives

| Area | Location |
| --- | --- |
| Experiment code | `comparison/` (adapters, shared agent, sandbox, recovery, tests) |
| Recorded run + evidence | `comparison/runs/2026-10-04-demo/` (`summary.json`, `config.json`, `costs.json`, `verification.json`, per-framework logs and records) |
| Upstream reference | `reference/inspect_ai/` — read-only snapshot, exact revisions in [`docs/reference-snapshots.md`](reference-snapshots.md) |
| Original examples | `Inspect_Eg_1/`, `Inpect Eg_2/` (starting material, kept as-is) |
| Tutorial + recorded run | `tutorial/` (`repair.py`, `fixed_tests.py`, `compose.yaml`, `first_eval.py`, `recorded/`) |
| Docs | this `docs/` bundle (tutorial, presentation, slides, results, runbook, review, changelog) |
| Session transcripts | `session-transcripts/10-04-2026/`, `session-transcripts/10-18-2026/` |
| The original conversation | `inspect-ai-conversation.md` |

## 11. Known gaps and open threads

- **Committed credential.** A DeepSeek API key remains in Git history inside `Inspect_Eg_1/Eval.py`. The user said they deleted the key; revocation at the provider was recommended and never confirmed. If that key was never revoked, rotate it.
- **README phase-table inaccuracy.** The table implies the `shared` phase makes no model calls; it does (the common agent's three repair attempts). Controls, recovery, and summary are the truly model-free phases.
- **Orphaned entry point.** `tutorial/first_eval.py` and its `mockllm/model` smoke-test path are referenced by no document — the natural zero-cost first step for learners is invisible.
- **No failure-path teaching material.** There is no checked-in failed repair to walk through, no exercises or variations, no multi-sample dataset or second model at tutorial level, and nothing that bridges the tutorial to the full `comparison/` experiment beyond prose.
- **Missing answer in the record.** The final question of the 2026-10-04 explanation sessions ("so in this experiment, are we proving the concept of integrated environments?") was saved only as a pre-reply snapshot; the answer survives, if anywhere, in the raw HTML export rather than the curated transcripts.
- **Untidy artifacts.** `tutorial/repair-logs/` duplicates the `recorded/` log; the `Inpect Eg_2` folder name carries its original typo; the known math-scorer defects in that example are documented but unfixed, deliberately, since it is third-party starting material.

Natural next tutorials, if the teaching work continues: document the mock smoke-test path as step zero; add a recorded *failed* run and a log-reading exercise on it; extend to a multi-sample dataset with `eval_set()` interruption/resume to demonstrate completed-task reuse live; and a bridging tutorial from `tutorial/repair.py` to the four-framework `comparison/`.

## Sources

Primary: [`inspect-ai-conversation.md`](../inspect-ai-conversation.md); [`docs/inspect-ai-review.md`](inspect-ai-review.md); [`docs/comparison-results.md`](comparison-results.md) and [`comparison/runs/2026-10-04-demo/`](../comparison/runs/2026-10-04-demo/summary.json); [`docs/inspect-ai-tutorial.md`](inspect-ai-tutorial.md); [`docs/inspect-ai-presentation.md`](inspect-ai-presentation.md); the recorded logs in [`tutorial/recorded/`](../tutorial/recorded/); the session transcripts under `session-transcripts/10-04-2026/` and `session-transcripts/10-18-2026/`; and the Git history (2026-10-04 through 2026-10-18). Upstream: [Inspect AI](https://inspect.aisi.org.uk/) (snapshot revision recorded in [reference snapshots](reference-snapshots.md)).
