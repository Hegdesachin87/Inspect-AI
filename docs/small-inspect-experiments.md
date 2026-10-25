---
type: guide
title: Five small Inspect AI experiments
description: Five minutes-scale, cents-scale hands-on experiments drawn from the official Inspect AI tutorial, docs, and examples, all runnable with a DeepSeek key and Docker.
timestamp: "2026-10-25T00:31:00-04:00"
---

# Five small Inspect AI experiments

Five small experiments selected from the official Inspect AI material, ranked by how much they teach per minute and per cent. Each cites its official source and the bundled example it uses. Every command below was smoke-tested in this repository on 2026-10-25 against `inspect-ai 0.3.276` (in `.venv-tutorial`) using the mock provider, so the syntax is verified — only the paid calls are left to run.

## Prerequisites

```bash
source .venv-tutorial/bin/activate          # inspect-ai 0.3.276, already set up
export OPENAI_API_KEY="$DEEPSEEK_API_KEY"   # DeepSeek key on the OpenAI-compatible provider
```

Throughout, `DS` means `--model openai/deepseek-chat --model-base-url https://api.deepseek.com`. Check which model names your account exposes and substitute accordingly:

```bash
curl -s https://api.deepseek.com/models -H "Authorization: Bearer $OPENAI_API_KEY"
```

Logs land in `./logs` by default; the commands below set explicit `--log-dir` folders. Only experiment 2 needs Docker. View any log with `inspect view --log-dir <dir> --port 7575`.

---

## 1. Same outputs, different judges — re-score one log without regenerating

**Question:** when the judge is a model instead of a test, how much does the verdict depend on *which* model judges — and on the model grading its own answers?

This is the cheapest real experiment in the ecosystem. Generate the agent transcripts once with `--no-score`, then re-score the same log with different scorers and different graders. No re-generation, ever ([scoring workflow: "this bypasses the entire generation phase"](https://inspect.aisi.org.uk/scoring-workflow.html)).

```bash
# Arm 0 — generate once, unscored (5 samples, ~5 calls)
inspect eval reference/inspect_ai/examples/theory_of_mind.py $DS \
  --limit 5 --no-score --log-dir logs/judge-exp

L=$(ls logs/judge-exp/*.eval | head -1)

# Arm 1 — deterministic scorer, free (no model calls)
inspect score "$L" --scorer includes --action append --overwrite

# Arm 2 — model judge, self-grading (deepseek-chat grades deepseek-chat; ~5 calls)
inspect score "$L" --scorer model_graded_fact --action append --overwrite

# Arm 3 — model judge, cross-grading (deepseek-reasoner grades deepseek-chat; ~5 calls)
inspect score "$L" --scorer model_graded_fact \
  --model openai/deepseek-reasoner --model-base-url https://api.deepseek.com \
  --action append --overwrite
```

**Measure:** compare the three accuracy columns in the viewer; open individual samples and read the judge's rationale under each scorer. Do self- and cross-grades agree? Where they disagree, which is right?

**Expect to find:** the deterministic `includes` matcher mis-scores open-ended answers (it cannot judge paraphrases — that limitation is the lesson); the model judge handles them, and self- vs cross-grading diverges on borderline samples. This is grader bias, measured on your own log for about a cent.

**Runnable version:** [`experiments/judge-swap/`](../experiments/judge-swap/README.md) — self-contained task, `run.sh` (all arms), `summarize.py` (judge matrix), and `judge-swap.pptx` (deck explaining the experiment).

**Sources:** [Scoring workflow](https://inspect.aisi.org.uk/scoring-workflow.html) · [Model-graded scorers](https://inspect.aisi.org.uk/model-graded.html) (self-grading default and `model_role` precedence) · example: [`reference/inspect_ai/examples/theory_of_mind.py`](../reference/inspect_ai/examples/theory_of_mind.py)

---

**z.ai note:** z.ai's OpenAI-compatible endpoint serves chat completions only — add `-M responses_api=false` or Inspect 0.3.276 calls `/responses` and gets a 404 (the run script does this for you). Verify account balance before a run: an unfunded key returns error 1113 on every model.

## 2. Human approval of a dangerous command

**Question:** what does tool-call governance look like when the agent tries something destructive — and can an allowlist policy handle the safe cases without pestering the human?

The bundled approval demo asks the model to demonstrate `ls` and `rm` (bash) and `shutil.rmtree` (python). The policy auto-approves allowlisted commands and escalates everything else to *you*, in the terminal, mid-run:

```bash
inspect eval reference/inspect_ai/examples/approval/approval.py \
  --approval reference/inspect_ai/examples/approval/approval.yaml \
  $DS --log-dir logs/approval-demo
```

Requires Docker and an interactive terminal. `ls` sails through the custom `bash_allowlist` approver; `rm` and `shutil.rmtree` arrive at your prompt — approve or reject each one, then read the log to see every decision recorded as a `ToolCallEvent` with its approval.

**Measure:** which commands were auto-approved, which escalated, and what the agent did after a rejection.

**Expect to find:** the run freezes exactly at the dangerous call and resumes after your decision — the core governance primitive for agentic AI, experienced rather than described. The two custom `@approver`s in [approval.py](../reference/inspect_ai/examples/approval/approval.py) are ~40 lines each and worth reading aloud in class.

**Sources:** [Approval mode](https://inspect.aisi.org.uk/approval.html) · example: [`reference/inspect_ai/examples/approval/`](../reference/inspect_ai/examples/approval/README.md)

---

## 3. Tool probe — does the reasoning model call the tool?

**Question:** given a trivial arithmetic question and an `add()` tool, does `deepseek-chat` behave differently from `deepseek-reasoner` — does either bother calling the tool or just answer?

Two runs, two calls total:

```bash
inspect eval reference/inspect_ai/examples/tool_use.py@addition_problem \
  --model openai/deepseek-chat   --model-base-url https://api.deepseek.com --log-dir logs/tool-probe
inspect eval reference/inspect_ai/examples/tool_use.py@addition_problem \
  --model openai/deepseek-reasoner --model-base-url https://api.deepseek.com --log-dir logs/tool-probe
```

**Measure:** open both logs in the viewer — did the model emit a `add` tool call or answer inline? Same answer either way? Token counts?

**Expect to find:** a small, real behavioral difference between two models you actually use, visible in ten seconds of log-reading. The same example file has `@bash`, `@read`, `@write`, and `@parallel_add` variants to push further.

**Sources:** [Tutorial: custom tools](https://inspect.aisi.org.uk/tutorial.html#sec-custom-tools) · [Tools reference](https://inspect.aisi.org.uk/tools.html) · example: [`reference/inspect_ai/examples/tool_use.py`](../reference/inspect_ai/examples/tool_use.py)

---

## 4. Cache A/B — the second run is free

**Question:** what does response caching actually buy, and how do you see it?

```bash
inspect eval reference/inspect_ai/examples/theory_of_mind.py $DS \
  --limit 5 --cache --log-dir logs/cache-exp     # run 1: pays for 5 calls
inspect eval reference/inspect_ai/examples/theory_of_mind.py $DS \
  --limit 5 --cache --log-dir logs/cache-exp     # run 2: replays from cache, ~0 cost

inspect cache list                               # see the cached entries
inspect cache clear                              # when you want a fresh start
```

**Measure:** compare token usage lines between the two runs (run 2 should show cache hits and near-zero new output tokens); confirm identical scores — cached replays are bit-identical.

**Expect to find:** reproducibility and cost control as first-class features: rerunning an experiment to inspect it differently should not re-spend. Note the distinction: Inspect's `--cache` (used here) is provider-agnostic; provider-side prompt caching (the `CW`/`CR` usage counters) is a separate, Anthropic-style mechanism.

**Sources:** [Caching](https://inspect.aisi.org.uk/caching.html) · example: [`reference/inspect_ai/examples/cache.py`](../reference/inspect_ai/examples/cache.py) (`CachePolicy` variants)

---

## 5. The smallest LLM-judge eval — theory of mind in five samples

**Question:** what does a model-graded evaluation actually look like end to end — and can you read the judge's reasoning, not just its verdict?

The classic official example, bundled dataset included, nothing to install beyond `inspect-ai`:

```bash
inspect eval reference/inspect_ai/examples/theory_of_mind.py $DS \
  --limit 5 --log-dir logs/tom
inspect view --log-dir logs/tom --port 7575
```

**Measure:** accuracy across the five samples; for each sample, the full judge chain — the `chain_of_thought` solver's reasoning, the answer, and the `model_graded_fact` grader's critique of that answer.

**Expect to find:** a complete judge eval — solver pipeline (`chain_of_thought()` + `generate()`), an LLM grader, scores with explanations — in a 22-line task file you can read in one screen. Pair it with experiment 1 to question the judge it just used.

**Sources:** [Model-graded scorers](https://inspect.aisi.org.uk/model-graded.html) · [Tutorial: benchmarks](https://inspect.aisi.org.uk/tutorial.html#sec-benchmarks) · example: [`reference/inspect_ai/examples/theory_of_mind.py`](../reference/inspect_ai/examples/theory_of_mind.py)

---

## Notes and limits

- All five run against the pinned `inspect-ai 0.3.276` already installed in `.venv-tutorial`; command syntax verified 2026-10-25 with the `mockllm/model` provider.
- The `reference/inspect_ai/` snapshot is read-only; these commands never write into it (logs go to your `--log-dir`).
- Total cost of all five experiments with DeepSeek: well under $0.10.
- The official docs are versioned live at [inspect.aisi.org.uk](https://inspect.aisi.org.uk/); the local snapshot (current `main` at capture, see [reference snapshots](reference-snapshots.md)) may be slightly ahead of 0.3.276.
- Bigger follow-ons when these feel small: the [coding-repair tutorial](inspect-ai-tutorial.md) with Docker sandboxes, the [four-framework comparison](experiment-report.md), or a [Terminal-Bench / SWE-bench subset run](experiment-report.md#11-known-gaps-and-open-threads) on real tasks.
