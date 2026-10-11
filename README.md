# Four-Framework Coding-Agent Comparison

A controlled, executable experiment that runs the **same** Python coding-repair agent through four LLM evaluation frameworks — **Inspect AI**, **Ragas**, **DeepEval**, and **MLflow** — and compares how each one wires up the experiment, executes it, scores the result, stores evidence, and reuses completed work after an interruption.

The point is **not** to find "the best framework." It is to measure, with real code and real model calls, how much execution infrastructure each framework supplies versus how much the application has to build itself.

---

## Table of contents

1. [What the project does](#what-the-project-does)
2. [The experiment in brief](#the-experiment-in-brief)
3. [Key findings](#key-findings)
4. [Repository layout](#repository-layout)
5. [Requirements](#requirements)
6. [Environment variables](#environment-variables)
7. [Setup](#setup)
8. [Running the project](#running-the-project)
9. [Understanding the phases](#understanding-the-phases)
10. [Outputs and where to find them](#outputs-and-where-to-find-them)
11. [Viewing results](#viewing-results)
12. [Troubleshooting](#troubleshooting)
13. [Interpreting results (caveats)](#interpreting-results-caveats)
14. [Cost](#cost)
15. [Further reading](#further-reading)

---

## What the project does

The experiment centers on a cooperative **coding-repair agent**: the model is given a small broken Python function, a `run_command` shell tool, and a fixed budget, and it must produce a corrected `/workspace/project.py`. Grading runs **after** the agent finishes, in a **separate** Docker container with fixed tests injected — so the agent can never edit the tests, and generated code never runs on the host.

Three repair tasks are used (defined in `comparison/cases.py`):

| Task | Requirement |
| --- | --- |
| `slug` | Fix `slug(text)`: lowercase ASCII letters, preserve ASCII digits, collapse runs of other characters into one hyphen, strip leading/trailing hyphens, empty input → empty string. |
| `intervals` | Fix `merge_intervals(intervals)`: merge overlapping/touching `[start, end]` pairs, return sorted, do **not** mutate input or nested pairs. |
| `chunks` | Fix `chunks(items, size)`: return successive slices including a final short slice, empty input → `[]`, raise `ValueError` when `size <= 0`, do not mutate input. |

Every live run uses the same requirements, starting source, system prompt, model, tool permissions, and call budget, so the frameworks are compared on **experiment wiring and evidence storage**, not on built-in judge quality.

---

## The experiment in brief

### Pass one — shared trajectories (grading only)

A single application agent (`comparison/agent.py`) produces three final projects and their full trajectories. All four frameworks then run their **custom executable scorer** against those exact same saved projects. Six extra controls verify that broken starting code fails and reference implementations pass. This pass makes **no model requests**.

### Pass two — live runs (each framework owns the experiment)

Each framework runs the repair experiment natively:

- **Inspect** uses its native dataset, solver generation, tool dispatch, Docker sandbox, scorer, and evaluation-set runner.
- **Ragas** uses `@experiment` plus a custom `discrete_metric`.
- **DeepEval** uses its traced dataset iterator plus a custom `BaseMetric`.
- **MLflow** uses `genai.evaluate(predict_fn=...)` plus a custom code-based scorer.

The last three all call the same application agent and the same custom Docker workspace code; Inspect supplies its own sandbox/tool machinery.

### Recovery experiment (no model calls)

A separate deterministic fixture test completes one repair callback, blocks during the next, gets interrupted (SIGINT, then SIGKILL after 30 s), and the same native runner is rerun against the same storage. This measures **reuse of already-completed tasks**, not mid-conversation agent checkpoint restoration.

---

## Key findings

From the recorded demo (see `docs/comparison-results.md`):

- **Inspect's advantage is integrated sandbox execution and completed-task reuse after interruption — not better grading.** All four SDKs returned identical grades for the same final projects.
- On interruption + rerun, **Inspect reused the completed task** and scheduled only the missing one; Ragas, DeepEval, and MLflow re-invoked already-completed callbacks in the tested configuration.
- MLflow's **tracing** was particularly useful for inspecting spans.
- If an application already owns its agent loop and environments, Ragas/DeepEval/MLflow can evaluate it without handing execution to Inspect.

This is a small demonstration, not a leaderboard.

---

## Repository layout

```
.
├── comparison/                     # The main Python package
│   ├── __init__.py
│   ├── run.py                      # CLI orchestrator (entry point)
│   ├── worker.py                   # Runs each framework in its own subprocess
│   ├── agent.py                    # Common OpenAI application agent (tool loop)
│   ├── cases.py                    # Three repair tasks + model budget constants
│   ├── sandbox.py                  # Docker sandbox (Workspace) + fixed-test grader
│   ├── inspect_runner.py           # Inspect AI adapter
│   ├── ragas_runner.py             # Ragas adapter
│   ├── deepeval_runner.py          # DeepEval adapter
│   ├── mlflow_runner.py            # MLflow adapter
│   ├── recovery.py                 # Interruption / reuse experiment
│   ├── requirements.in             # Direct, hand-pinned dependencies
│   ├── requirements.lock           # Full pinned dependency resolution
│   ├── runs/                       # Experiment outputs (gitignored)
│   └── tests/
│       └── test_comparison.py      # Unit tests (grading + sandbox isolation)
├── docs/
│   ├── index.md
│   ├── comparison-runbook.md       # Authoritative run instructions
│   ├── comparison-results.md       # Recorded demo results + interpretation
│   ├── inspect-ai-review.md        # Review + comparison plan
│   ├── reference-snapshots.md      # Upstream source revisions
│   └── log.md
├── reference/                      # Read-only upstream Inspect source snapshot
├── Inspect_Eg_1/                   # Original Inspect example
├── Inpect Eg_2/                    # Original Inspect example (2)
├── inspect-ai-conversation.md      # Original conversation transcript
├── session-transcripts/
├── .gitignore
└── .venv-comparison/               # Virtual environment (created during setup, gitignored)
```

---

## Requirements

- **Python 3.12** (a 3.12 interpreter is available via `uv`)
- **`uv`** (recommended) — or any Python 3.12 toolchain with `pip`
- **Docker** with a working daemon:
  - Windows: **Docker Desktop** (Linux containers)
  - macOS/Linux: **Docker** or **Colima**
- **OpenAI API key** (only required for live model runs; controls/recovery/tests do not call the model)

Pinned SDK versions (from `comparison/requirements.in`):

| Package | Version |
| --- | --- |
| inspect-ai | 0.3.276 |
| ragas | 0.4.3 |
| deepeval | 4.2.8 |
| mlflow | 3.16.1 |
| openai | 3.3.0 |
| langchain-community | 0.3.31 (pinned for Ragas compatibility) |

The model is `gpt-4o-mini-2024-07-18` with temperature 0, at most **6 model calls per case** and **700 output tokens per call**.

---

## Environment variables

| Variable | Required for | Description |
| --- | --- | --- |
| `DOCKER_HOST` | All Docker phases | **Windows:** `npipe:////./pipe/docker_engine`. **macOS/Colima:** `unix://$HOME/.colima/inspect-comparison/docker.sock`. The runner defaults to the Colima socket, so on Windows this must be set explicitly. |
| `OPENAI_API_KEY` | Live runs (and Inspect init) | Your OpenAI key. Inspect requires the variable to *exist* even for no-call phases; a placeholder works for controls/recovery. |
| `COMPARISON_IMAGE` | Optional | Pin the exact Docker image digest for reproduction. If unset, the runner resolves the digest of a pulled `python:3.12-slim`. |
| `PYTHONUTF8` | Windows | Set to `1` to avoid a `cp1252` encoding crash in DeepEval/rich console output. |

The worker also sets `RAGAS_DO_NOT_TRACK`, `DEEPEVAL_TELEMETRY_OPT_OUT`, `MLFLOW_DISABLE_TELEMETRY`, etc. automatically to keep evaluation data local.

---

## Setup

Run everything from the repository root.

### 1. Create the virtual environment (Python 3.12)

```bash
uv venv --python 3.12 .venv-comparison
```

### 2. Install pinned dependencies

**Windows:**

```bash
uv pip install --python .venv-comparison/Scripts/python.exe -r comparison/requirements.lock
```

**macOS/Linux:**

```bash
uv pip install --python .venv-comparison/bin/python -r comparison/requirements.lock
```

### 3. Configure Docker

**Windows (Docker Desktop):**

```powershell
$env:DOCKER_HOST = "npipe:////./pipe/docker_engine"
docker pull python:3.12-slim
```

**macOS (Colima), from a shell:**

```bash
previous_context=$(docker context show)
colima start --profile inspect-comparison --cpu 2 --memory 2 --disk 8
docker context use "$previous_context"
export DOCKER_HOST="unix://$HOME/.colima/inspect-comparison/docker.sock"
docker pull python:3.12-slim
```

Optional — pin the exact image for byte-for-byte reproduction:

```bash
export COMPARISON_IMAGE='python@sha256:02108f5d322dd89f1c9e552442c25acb0543dfdbc455693a5599624f20d9155d'
docker pull "$COMPARISON_IMAGE"
```

### 4. Set your OpenAI API key

```powershell
# PowerShell
$env:OPENAI_API_KEY = "sk-..."
```

```bash
# Bash
export OPENAI_API_KEY="sk-..."
```

> Only needed for live runs. For controls/recovery/tests you can use a placeholder like `"sk-placeholder"` because no model call is made.

---

## Running the project

The entry point is always:

```
.venv-comparison/Scripts/python.exe -m comparison.run <options>    # Windows
.venv-comparison/bin/python -m comparison.run <options>            # macOS/Linux
```

(Substitute `.venv-comparison/bin/python` for `Scripts/python.exe` on macOS/Linux throughout.)

### Step 1 — Unit tests (no API key, no cost)

Verifies grading logic, call budget, and sandbox isolation (no host mounts, no network, no credentials).

```bash
.venv-comparison/Scripts/python.exe -m unittest discover -s comparison/tests -v
```

Expected: 5 tests, `OK`.

### Step 2 — Controls phase (no API key, no cost)

Grades broken vs. reference code through all four frameworks. Confirms your Docker sandboxes and every adapter work end to end before spending anything.

```bash
.venv-comparison/Scripts/python.exe -m comparison.run --phase controls --output comparison/runs/controls-only
```

Expected: `START`/`END ... exit 0` for all four frameworks.

### Step 3 — Recovery phase (no API key, no cost)

Tests interrupted-run reuse with deterministic fixtures.

```bash
.venv-comparison/Scripts/python.exe -m comparison.run --phase recovery --output comparison/runs/recovery-only
```

> Recovery requires a **fresh output directory** each time; its interruption markers cannot be reused.

### Step 4 — Live run, one framework (costs tokens)

Start small to keep cost minimal:

```bash
.venv-comparison/Scripts/python.exe -m comparison.run --phase live --framework inspect --output comparison/runs/inspect-only
```

Valid `--framework` values: `inspect`, `ragas`, `deepeval`, `mlflow`.

### Step 5 — Full run (all phases, costs tokens)

```bash
.venv-comparison/Scripts/python.exe -m comparison.run --output comparison/runs/my-run
```

This runs shared + live + recovery, spends tokens on the 15 repair attempts (3 common-agent + 3 per framework), and prints a normalized `summary.json` report at the end.

### Step 6 — Rebuild the summary from existing artifacts (no Docker, no cost)

```bash
.venv-comparison/Scripts/python.exe -m comparison.run --phase summary --output comparison/runs/my-run
```

Use this to re-generate `summary.json` after inspecting artifacts — never rerun live phases just to view results.

---

## Understanding the phases

| Phase | Model calls? | What it does |
| --- | --- | --- |
| `controls` | No | Grades each task's broken source and reference implementation through all four frameworks; raises if a control is mis-graded. |
| `shared` | No | A common agent's saved trajectories are graded identically by each framework (verifies adapter/scorer parity). |
| `live` | **Yes** | Each framework runs the actual repair experiment with its own native machinery. |
| `recovery` | No | Deterministic fixtures + process interruption + rerun to test completed-task reuse. |
| `summary` | No | Rebuilds the normalized report from existing phase artifacts. |
| `all` | **Yes** | Default; runs `shared`, `live`, and `recovery`, then summarizes. |

You can combine flags, e.g. `--phase shared --framework mlflow`.

---

## Outputs and where to find them

`summary.json` is the normalized comparison. Native SDK artifacts live alongside it:

- **Inspect** `.eval` logs → each Inspect phase's `logs/` directory.
- **Ragas** datasets and experiment JSONL → `backend/`.
- **DeepEval** native test-run JSON → `native-results/`.
- **MLflow** SQLite storage, trace artifacts, native export, and `trace-verification.json`.
- **Final source, messages, tool results, token usage, model-call counts** → each live phase's `records/` directory.
- **Recovery** interruption markers, native logs, and `fixture-invocations.jsonl`.

Other key files:

- `config.json` — recorded model, budget, system prompt, image digest, and versions.
- `controls.json` / `shared-records.json` — the shared, model-free inputs.

The SQLite DB and bulky MLflow artifact directories are gitignored; the committed native JSON exports retain traces and scores for review.

---

## Viewing results

### Inspect log viewer

```bash
.venv-comparison/Scripts/inspect.exe view --log-dir comparison/runs/my-run/live/inspect/logs
```

### MLflow UI

```bash
.venv-comparison/Scripts/mlflow.exe ui \
  --backend-store-uri "sqlite:///$PWD/comparison/runs/my-run/live/mlflow/mlflow.db" \
  --host 127.0.0.1 --port 5001
```

Then open http://127.0.0.1:5001 in a browser. The comparison does not launch either server automatically.

---

## Troubleshooting

### `PrerequisiteError: No OPENAI_API_KEY ... defined in the environment`

Inspect initializes its OpenAI model client even for no-call phases. Set the variable (a placeholder is fine for controls/recovery):

```powershell
$env:OPENAI_API_KEY = "sk-placeholder"
```

### Docker connection fails on Windows

The runner defaults `DOCKER_HOST` to a macOS Colima socket. Point it at Docker Desktop:

```powershell
$env:DOCKER_HOST = "npipe:////./pipe/docker_engine"
```

### DeepEval/rich crashes with `cp1252` encode error

Rich's legacy Windows console path can't encode Unicode table symbols. Force UTF-8:

```powershell
$env:PYTHONUTF8 = "1"
```

(Running inside **Windows Terminal** avoids this entirely.)

### `openai.AuthenticationError: 401 Incorrect API key`

The key is invalid/revoked/truncated, or it belongs to a different provider. Verify it:

```powershell
curl.exe -s https://api.openai.com/v1/models -H "Authorization: Bearer $env:OPENAI_API_KEY"
```

A JSON list of models means the key works.

### Recovery fails with "use a fresh output directory"

Recovery interruption markers and invocation history cannot be reused. Always pass a new `--output`.

### Remember to re-set env vars in new terminals

Each new PowerShell/Bash session needs `DOCKER_HOST`, `PYTHONUTF8` (Windows), and `OPENAI_API_KEY` (for live runs) set again.

---

## Interpreting results (caveats)

- **Temperature 0 does not guarantee identical outputs.** SDK request serialization and tool-schema generation differ, so trajectories can diverge even with "equal" settings. A different score in this small demo does not mean a framework makes the model smarter.
- **This compares experiment wiring, evidence storage, and reuse — not built-in RAG metrics or model judges.** All setups use the same custom fixed-test grader (`comparison/sandbox.py`).
- **The grader is for cooperative repairs**, not adversarial anti-cheating. Three hand-written tasks and their listed test cases are not an exhaustive correctness benchmark.
- **Latency is not compared** (imports, caching, and sandbox startup differ).

For the full interpretation, see `docs/comparison-results.md`.

---

## Cost

Using published GPT-4o-mini prices, the recorded demo's total model usage was roughly **one cent** (~$0.01): about $0.0016 for common-agent trajectories, ~$0.0066 for all four live phases, plus a small failed-setup attempt. Exact token-based calculations are in `comparison/runs/2026-10-04-demo/costs.json`. Controls, scoring, and recovery do **not** call a model.

---

## Further reading

- [Runbook](docs/comparison-runbook.md) — authoritative setup and reproduction commands.
- [Results](docs/comparison-results.md) — measured grades, recovery behavior, token costs, and integration costs.
- [Review & comparison plan](docs/inspect-ai-review.md) — original rationale and design.
- [Reference snapshots](docs/reference-snapshots.md) — upstream source URLs and revisions.
- [Conversation transcript](inspect-ai-conversation.md) — the original discussion that motivated the project.
