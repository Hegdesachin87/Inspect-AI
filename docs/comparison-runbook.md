---
type: guide
title: Run the four-framework coding-agent comparison
description: Reproduce the shared-trajectory, live coding-repair, and interrupted-run experiments with pinned SDK dependencies.
timestamp: 2026-10-04T13:38:00-04:00
---

# Run the four-framework coding-agent comparison

## What runs

The code is in [comparison/](../comparison/). Three repair tasks cover slug formatting, interval merging without mutation, and list chunking with invalid-size handling. Every live run uses the same task requirements, starting source, system prompt, model, tool permissions, and call budget.

The two evaluation passes are:

1. A common application agent creates three final projects and trajectories. Each SDK grades those exact projects with the same executable tests. Six extra controls check that broken starting code fails and reference implementations pass.
2. Each SDK runs the repair experiment. Inspect uses its native dataset, solver generation, tool dispatch, Docker sandbox, scorer, and evaluation-set runner. Ragas uses `@experiment`; DeepEval uses its traced dataset iterator; MLflow uses `genai.evaluate(predict_fn=...)`. These three call the same application agent and custom Docker workspace code.

The recovery experiment is separate. It uses deterministic successful repairs, not model calls, interrupts each process during its second callback, and reruns the same native runner against the same storage. It tests reuse of completed tasks, not continuation of an agent's unfinished conversation.

## Setup

Run from the repository root. Use Python 3.12 and a working Docker daemon with Docker Compose.

```bash
uv venv --python 3.12 .venv-comparison
uv pip install --python .venv-comparison/bin/python -r comparison/requirements.lock
```

For Colima on this Mac, use a dedicated profile and restore the previous global Docker context after startup:

```bash
previous_context=$(docker context show)
colima start --profile inspect-comparison --cpu 2 --memory 2 --disk 8
docker context use "$previous_context"
export DOCKER_HOST="unix://$HOME/.colima/inspect-comparison/docker.sock"
```

The observed image is pinned below. For exact reproduction, pull it and set the override:

```bash
export COMPARISON_IMAGE='python@sha256:02108f5d322dd89f1c9e552442c25acb0543dfdbc455693a5599624f20d9155d'
docker pull "$COMPARISON_IMAGE"
```

Without `COMPARISON_IMAGE`, the runner resolves the digest of an already-pulled `python:3.12-slim` image and records it. Other Docker installations can set `DOCKER_HOST` for their own daemon. On this Mac, the default is the dedicated Colima socket.

Supply `OPENAI_API_KEY` through the environment, without putting it in source or command history. The model is `gpt-4o-mini-2024-07-18`. Nothing reads the credential from the old example script. The comparison uses at most six model calls per case with 700 output tokens per call and temperature zero. These are the demo's explicit spending limits, not defaults claimed for any framework.

Ragas 0.4.3 imports a VertexAI module missing from langchain-community 0.4.2. The dependency file therefore pins langchain-community 0.3.31. The full installed resolution is in `comparison/requirements.lock`.

## Run

Use a fresh output directory for a full run. This spends model tokens on fifteen repair attempts, three common-agent attempts and three attempts per framework.

```bash
.venv-comparison/bin/python -m unittest discover -s comparison/tests -v
.venv-comparison/bin/python -m comparison.run --output comparison/runs/my-run
```

Each SDK runs in a separate subprocess so tracing hooks and event-loop changes do not affect another framework. Workers disable Ragas, DeepEval, and MLflow analytics and keep experiment artifacts local. The model receives prompts and tool outputs. Setup downloads packages and container images. This session also used a separate status monitor that sent changed job-log evidence to its remote judge.

You can run a single phase or SDK:

```bash
.venv-comparison/bin/python -m comparison.run --phase controls --output comparison/runs/controls-only
.venv-comparison/bin/python -m comparison.run --phase live --framework inspect --output comparison/runs/inspect-only
.venv-comparison/bin/python -m comparison.run --phase recovery --output comparison/runs/recovery-only
```

The controls and recovery phases make no model requests. In recovery, the controller tries SIGINT first and escalates to SIGKILL if a blocked fixture callback does not exit within 30 seconds. That operational timeout is not a scoring threshold. Existing recovery directories cannot be reused because their interruption markers and invocation history would mix trials.

`summary.json` is a normalized comparison. SDK artifacts remain alongside it:

- Inspect `.eval` logs under each Inspect phase's `logs/` directory.
- Ragas datasets and experiment JSONL under `backend/`.
- DeepEval native test-run JSON under `native-results/`.
- MLflow SQLite storage, trace artifacts, a native result export, and `trace-verification.json`.
- Final source, messages, tool results, token usage, and model-call counts under each live phase's `records/` directory.
- Recovery interruption markers, native logs, and `fixture-invocations.jsonl`.

The SQLite database, bulky MLflow artifact directories, package environment, and setup scratchpad are excluded from Git. The committed native JSON exports retain traces and scores for review. The MLflow viewer command below uses the local database created by executing the experiment, so a fresh clone must run the experiment first.

Run `--phase summary` to rebuild the normalized report from existing phase artifacts. This phase reads files and does not require Docker. Do not rerun live phases merely to display results. Ragas, DeepEval, and MLflow will generate another set of model outputs in this configuration; Inspect can reuse completed evaluation tasks.

## Inspect the results

For the recorded demonstration, read [the results report](comparison-results.md) and [summary.json](../comparison/runs/2026-10-04-demo/summary.json).

Inspect logs can be opened with the installed viewer:

```bash
.venv-comparison/bin/inspect view --log-dir comparison/runs/2026-10-04-demo/live/inspect/logs
```

MLflow's local UI can display its live traces:

```bash
.venv-comparison/bin/mlflow ui \
  --backend-store-uri "sqlite:///$PWD/comparison/runs/2026-10-04-demo/live/mlflow/mlflow.db" \
  --host 127.0.0.1 --port 5001
```

The comparison does not launch either server automatically. The dedicated VM was stopped after the recorded run, with no experiment containers left behind and the original global Docker context restored. After future runs, stop the dedicated VM with `colima stop --profile inspect-comparison`.

## Grading and isolation

Agent containers have no network or host mounts, run as UID 1000, have read-only root filesystems, and use writable temporary workspaces. They do not receive API credentials. Shell commands have a timeout. The scorer runs the final source in another restricted container with fixed tests injected after the agent is finished. It never executes generated source on the host.

Docker's file-copy interface could not read the temporary filesystem in the first Inspect attempt. The adapter now extracts source through `sandbox().exec(['cat', ...])`, matching the application runner's mechanism. The initial failed attempt and its token usage are preserved rather than silently discarded.

This is cooperative coding-repair evaluation, not a hardened adversarial grading system. A malicious Python module could interfere with tests that execute in the same Python process. Three hand-written tasks and their listed test cases are not an exhaustive correctness benchmark.

## How to interpret a difference

Equal semantic settings do not make requests byte-identical. Inspect uses its own provider serialization and tool schema generation. The other stacks share the application's OpenAI request serializer. Native schemas, tool messages, provider caching, and stochastic generation can change trajectories. A different score in this small demo does not establish that a framework makes the model smarter.

All setups use the same custom fixed-test grader. This experiment does not compare the quality of their built-in RAG metrics or model judges. It compares experiment wiring, evidence storage, and reuse of completed work for this particular agent task.

The MLflow adapter explicitly disables prediction trace validation after decorating the callback with `@mlflow.trace`. That validation otherwise invokes the prediction function an extra time. Persisted traces are checked after evaluation. The native evaluation output is read from `result.result_df`, and its record column is `response` in MLflow 3.16.1.

The Ragas metric is awaited with `ascore` inside the asynchronous experiment callback. The synchronous `score` path triggered an event-loop error in the initially installed setup. Callback row completeness is checked because this Ragas runner logs individual callback exceptions and continues.

## Sources checked

- [Inspect sandboxing](https://inspect.aisi.org.uk/sandboxing.html) and [evaluation sets](https://inspect.aisi.org.uk/eval-sets.html).
- [Ragas experiment quickstart](https://docs.ragas.io/en/stable/getstarted/experiments_quickstart/) and [agent tutorial](https://docs.ragas.io/en/stable/tutorials/agent/).
- [DeepEval custom metrics](https://deepeval.com/docs/metrics-custom) and [traced component evaluation](https://deepeval.com/docs/evaluation-component-level-llm-evals).
- [MLflow code-based scorers](https://mlflow.org/docs/latest/genai/eval-monitor/scorers/custom/) and the tracing guide bundled with MLflow 3.16.1.

The implementation follows the installed SDK APIs where documentation examples differ. It does not modify the read-only upstream Inspect snapshot.
