---
type: experiment
title: Inspect, Ragas, DeepEval, and MLflow comparison results
description: Measured shared-trajectory grades, live coding-repair outcomes, SDK integration requirements, and interrupted-run recovery from the four-framework demo.
timestamp: 2026-10-04T13:44:00-04:00
---

# Inspect, Ragas, DeepEval, and MLflow comparison results

## Result

Inspect's demonstrated advantage was integrated sandbox execution and reuse of completed evaluation tasks after interruption. It did not grade answers better in this experiment. All four SDKs supported the experiment and returned identical grades for the same final projects.

This was a small, executed demonstration, not a framework leaderboard. Three hand-written tasks and one live trial per framework cannot establish performance differences.

## Experiment

The agent repaired Python functions for slug formatting, interval merging, and list chunking. The fixed tests checked requirements including empty inputs, touching intervals, unchanged input lists, incomplete final chunks, and invalid chunk sizes.

The agent's shell ran in a restricted Docker container with no network, credentials, or host mounts. Grading ran afterward in a separate container, so the agent could not edit the test files. The grader evaluated the resulting code, rather than accepting the agent's assertion that it was done.

Every setup used `gpt-4o-mini-2024-07-18`, temperature zero, the same requirements and starting files, the same shell tool, and a limit of six model calls with 700 output tokens per call. SDK request serialization differs, so this is semantic parity rather than byte-identical requests.

Installed versions were Inspect AI 0.3.276, Ragas 0.4.3, DeepEval 4.2.8, MLflow 3.16.1, and OpenAI SDK 3.3.0. Python was 3.12.11. Full dependencies and the Docker image digest are recorded in the [run configuration](../comparison/runs/2026-10-04-demo/config.json) and `comparison/requirements.lock`.

## Pass one: the same saved projects

One application agent produced three projects and their trajectories. All four frameworks then ran their custom executable scorer against those exact projects.

Each framework returned:

- Slug repair: pass.
- Interval repair: fail.
- Chunk repair: pass.
- All three intentionally broken controls: fail.
- All three reference implementations: pass.

Thus each gave the common agent 2 of 3 passes and correctly classified all six controls. The same result is expected when the same deterministic grader sees the same source. This verifies the adapters and result recording; it does not compare built-in judge quality.

The interval repair sorted the outer list but retained a reference to an original nested pair. Merging changed that pair in the caller's input. The scorer detected the mutation despite the agent's claim that its fix did not mutate input.

Evidence: [shared records and trajectories](../comparison/runs/2026-10-04-demo/shared-records.json), plus normalized scores for [Inspect](../comparison/runs/2026-10-04-demo/shared/inspect/scores.json), [Ragas](../comparison/runs/2026-10-04-demo/shared/ragas/scores.json), [DeepEval](../comparison/runs/2026-10-04-demo/shared/deepeval/scores.json), and [MLflow](../comparison/runs/2026-10-04-demo/shared/mlflow/scores.json).

## Pass two: each framework runs the experiment

| Framework | Slug | Intervals | Chunks | Passed | Input tokens | Output tokens |
| --- | --- | --- | --- | --- | ---: | ---: |
| Inspect | Pass | Fail | Pass | 2 of 3 | 7,951 | 740 |
| Ragas | Fail | Fail | Pass | 1 of 3 | 8,095 | 789 |
| DeepEval | Pass | Fail | Pass | 2 of 3 | 7,919 | 754 |
| MLflow | Pass | Fail | Pass | 2 of 3 | 7,919 | 765 |

Each setup made 18 model calls, using the full six-call allowance on every task. The Ragas run produced invalid Python for the slug task after shell quoting errors. Every interval run failed the input-mutation requirement.

Do not interpret Ragas's lower score as a framework defect. These are separate generations, including among the three setups that share the exact application agent. Temperature zero does not guarantee identical outputs. SDK serialization and tool-schema differences further limit comparisons involving Inspect.

Evidence: [normalized summary](../comparison/runs/2026-10-04-demo/summary.json) and live scores for [Inspect](../comparison/runs/2026-10-04-demo/live/inspect/scores.json), [Ragas](../comparison/runs/2026-10-04-demo/live/ragas/scores.json), [DeepEval](../comparison/runs/2026-10-04-demo/live/deepeval/scores.json), and [MLflow](../comparison/runs/2026-10-04-demo/live/mlflow/scores.json). Final projects and transcripts are in each framework's adjacent `records/` directory. Inspect's normalized token totals were checked against its native sample logs.

## Interruption and recovery

A separate deterministic fixture test completed one repair callback, blocked during the next callback, interrupted the process, then reran the same native runner using the same storage. There were no model requests in this test.

All four blocked processes required SIGKILL after the initial SIGINT did not stop them within 30 seconds. All four subsequently restarted successfully.

| Framework | Callbacks invoked after restart | Already completed callback repeated? |
| --- | --- | --- |
| Inspect | Intervals only | No |
| Ragas | Intervals and slug | Yes, intervals |
| DeepEval | Slug and intervals | Yes, slug |
| MLflow | Slug and intervals | Yes, slug |

Inspect's `eval_set()` reused the completed slug task and scheduled only the missing interval task. The other runners invoked both application callbacks again in the tested configuration.

This is evidence of Inspect's completed-task reuse, not proof of mid-conversation agent checkpoint restoration. It also does not mean the other frameworks cannot resume work with application checkpoints, dataset filtering, or additional configuration. DeepEval scoring cache was explicitly disabled; avoiding scoring does not by itself avoid calling an application to generate a fresh output.

Evidence: [recovery summary](../comparison/runs/2026-10-04-demo/recovery/summary.json). Each framework's recovery directory contains callback invocation history, interruption markers, and native logs.

## What code each framework supplied

Inspect supplied per-sample starting files and Docker provisioning through its task definition. Its native generation function dispatched tool calls. Its evaluation-set runner handled completion tracking and reuse. The experiment still needed a shell-tool wrapper, the fixed-test scorer, and an explicit bounded solver to match the common call budget.

Ragas's `@experiment` ran the callback, iterated the dataset, applied the custom metric, and saved local JSONL results. The application supplied its model/tool loop, Docker provisioning and cleanup, and source extraction.

DeepEval's traced dataset iterator ran the application and applied the custom metric. It saved native test-run results and attached the application's full recorded messages to the output. This implementation traced the root agent; it did not wire separate per-tool spans. DeepEval supports component tracing, so that omission is not a capability limitation.

MLflow's `genai.evaluate(predict_fn=...)` scheduled the application, applied the custom scorer, stored feedback and experiment data, and traced the agent and OpenAI calls. Its persisted live traces were verified: three agent traces, each with six model-call child spans, 21 spans total. The application still supplied Docker execution and the model/tool loop. See [trace verification](../comparison/runs/2026-10-04-demo/live/mlflow/trace-verification.json).

All four used the same custom grader in [sandbox.py](../comparison/sandbox.py). Inspect eliminated the need for the custom `Workspace` class and the application's tool-dispatch loop, but it did not eliminate task-specific grading code. No line-count proxy or unmeasured engineering-time claim is used here.

## Integration problems encountered

These were fixed and are part of the comparison's engineering cost:

- Ragas's loose dependency range selected langchain-community 0.4.2, which removed a module Ragas imports. Pinning 0.3.31 restored import compatibility.
- Calling Ragas's synchronous metric `score()` from the asynchronous experiment callback triggered an event-loop error. Awaiting `ascore()` resolved it.
- The initial MLflow adapter used an older result-table name. MLflow 3.16.1 exposes `result_df` with a `response` record column. The adapter now uses that API.
- MLflow prediction trace validation invokes the application an extra time by default. Since the callback is explicitly traced, the adapter skips that validation to avoid an extra paid repair, then verifies stored traces afterward.
- Inspect's Docker file-copy reader failed to extract files from the temporary filesystem, despite shell reads working. The corrected adapter extracts through sandbox execution. The original failed attempt and all of its token usage are retained in `comparison/runs/2026-10-04-demo/setup-failures/inspect-tmpfs-copy/`.

The original full-run process exited nonzero because of that Inspect extraction error. After fixing extraction, the Inspect live phase was rerun successfully and the normalized summary was rebuilt. The remaining original phases, including recovery, completed successfully. The report uses the corrected live attempt and accounts separately for the failed attempt rather than treating it as a model failure.

## Cost

Using the [documented GPT-4o-mini prices](https://developers.openai.com/api/docs/models/gpt-4o-mini), $0.15 per million input tokens and $0.60 per million output tokens:

- Common-agent trajectories: estimated $0.001639.
- All four successful live phases combined: estimated $0.006611.
- Failed Inspect setup attempt: estimated $0.001688.
- Connection preflight: estimated $0.000003.
- Total model usage: estimated $0.009941, about one cent.

These are token-based estimates, not an account invoice. No cached-input discount was applied. Package downloads, local computing, and separate status-monitor requests are excluded. Scoring and deterministic recovery did not call a model. Exact calculations are saved in [costs.json](../comparison/runs/2026-10-04-demo/costs.json).

## Checks and limits

Five automated tests passed. They check the declared model-call budget and early stopping, that grading accepts reference implementations and rejects bugs, that invalid Python fails grading, and that the application sandbox has no host mounts, credentials, or network and is removed after use. All frameworks correctly classified the six grading controls. No generated code executed on the host. [Verification evidence](../comparison/runs/2026-10-04-demo/verification.json) includes the test output, common-score agreement, budget checks, and native trace counts. The dedicated Docker VM was stopped after the experiment.

The grader is intended for cooperative coding repairs, not malicious attempts to subvert the Python test process. The tests cover the listed requirements with selected cases, not every possible input. Run latency was recorded but is not used as a performance comparison because imports, initial storage setup, caching, and sandbox startup differ.

## Recommendation

Choose Inspect when the evaluation must create environments, expose tools, grade actions or final files, and resume a collection of agent tasks. This demo supports that narrower advantage.

If an application already owns its agent loop and environments, Ragas, DeepEval, or MLflow can evaluate it without handing execution to Inspect. MLflow's tracing was particularly useful here, and the experiment gives no reason to replace a working application evaluation stack merely for a different score viewer.

For reproduction and viewer commands, use the [runbook](comparison-runbook.md). For the original rationale, see the [comparison plan](inspect-ai-review.md).
