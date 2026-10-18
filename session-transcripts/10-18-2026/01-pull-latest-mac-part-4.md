---
type: "transcript"
title: "Inspect-AI teaching scope"
description: "Verbatim user prompts and assistant responses from an agent session, with tool calls and thinking condensed."
timestamp: "2026-10-18T16:13:31+00:00"
source: "2026-10-18T16-09-38-645Z_01a14fc6-9c55-7c56-89ad-806a065c7a8c.jsonl"
---

# Inspect-AI teaching scope

Source: 2026-10-18T16-09-38-645Z_01a14fc6-9c55-7c56-89ad-806a065c7a8c.jsonl (pi) · Session: 01a14fc6-9c55-7c56-89ad-806a065c7a8c

Prompts and responses are copied verbatim. Quoted *Activity* lines are editorial summaries of tool calls and model thinking, not source text.

## Prompt 1

pull latest on https://github.com/Hegdesachin87/Inspect-AI.git

## Response 1

> *Activity:* Checked the repository and remote, pulled main without changing untracked files, and read transcript instructions.

Pulled the latest `main` successfully, now at `d890d8d`. Your untracked `.DS_Store` files were left untouched.


> *Activity:* Exported, checked, committed, and pushed session transcripts using the documented tooling.

Pulled latest `main` successfully. Local files were preserved. Session transcript saved and pushed.

## Prompt 2

can you give me the demo, how to run it?

## Response 2

> *Activity:* Read the project README, runbook, and runner code; checked installed tools, saved logs, and viewer commands.

The recorded demo is already on this Mac, so you can view it without Docker or API calls. I also checked the fresh-run commands. The current model is `deepseek-flash`, and the `shared` phase does make model calls despite what the README's phase table says.


> *Activity:* Exported, checked, committed, and pushed session transcripts using the documented tooling.

### View the recorded demo

No Docker or API key needed. Run:

```bash
cd /Users/ankitsingh/dev/Inspect-AI

.venv-comparison/bin/inspect view \
  --log-dir comparison/runs/2026-10-04-demo/live/inspect/logs \
  --port 7575
```

Open **http://localhost:7575**. Select a task to see the broken Python code, the agent's commands and repairs, and its test score.

### Run a fresh comparison

This runs three repair tasks through Inspect, Ragas, DeepEval, and MLflow, then tests recovery after interruption. It makes paid model calls.

Your virtual environment already exists. Start Docker:

```bash
previous_context=$(docker context show)
colima start --profile inspect-comparison --cpu 2 --memory 2 --disk 8
docker context use "$previous_context"

export DOCKER_HOST="unix://$HOME/.colima/inspect-comparison/docker.sock"
docker pull python:3.12-slim
```

Enter a **DeepSeek API key**, matching the current `deepseek-flash` model:

```bash
export OPENAI_BASE_URL="https://api.deepseek.com"
printf 'DeepSeek API key: '
read -r -s OPENAI_API_KEY
export OPENAI_API_KEY
echo
```

Run all four frameworks:

```bash
RUN="comparison/runs/demo-$(date +%Y%m%d-%H%M%S)"
.venv-comparison/bin/python -m comparison.run --output "$RUN"
```

Results go into `$RUN/summary.json`. To inspect the new agent conversations:

```bash
.venv-comparison/bin/inspect view \
  --log-dir "$RUN/live/inspect/logs" --port 7575
```

Stop the earlier viewer with `Ctrl+C` before reusing its port.

## Prompt 3

what is the demo?

## Response 3

> *Activity:* Exported, checked, committed, and pushed session transcripts using the documented tooling.

The demo compares **four frameworks running the same AI coding-repair task**: Inspect AI, Ragas, DeepEval, and MLflow.

The AI receives broken Python code and a shell tool. It must fix three functions:
- Turn text into a URL slug.
- Merge overlapping intervals.
- Split a list into chunks.

Fixed tests check each repair. You can inspect the agent's conversation, commands, final code, and scores.

The demo also interrupts runs and restarts them to see which frameworks reuse completed work.

**The point is to compare how the frameworks run, record, and resume experiments, not which makes the AI smarter.**

## Prompt 4

we are supposed to teach InspectAI, dos this tutorial explain that?

## Response 4

> *Activity:* Exported, checked, committed, and pushed session transcripts using the documented tooling.
