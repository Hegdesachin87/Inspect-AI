---
type: "transcript"
title: "Live DeepSeek tutorial and Inspect environments"
description: "Verbatim user prompts and assistant responses from an agent session, with tool calls and thinking condensed."
timestamp: "2026-10-18T16:21:28+00:00"
source: "2026-10-18T16-09-38-645Z_01a14fc6-9c55-7c56-89ad-806a065c7a8c.jsonl"
---

# Live DeepSeek tutorial and Inspect environments

Source: 2026-10-18T16-09-38-645Z_01a14fc6-9c55-7c56-89ad-806a065c7a8c.jsonl (pi) · Session: 01a14fc6-9c55-7c56-89ad-806a065c7a8c

Prompts and responses are copied verbatim. Quoted *Activity* lines are editorial summaries of tool calls and model thinking, not source text.

## Prompt 1

pull latest on https://github.com/Hegdesachin87/Inspect-AI.git

## Response 1

> *Activity:* Checked repository status and pulled main, preserving untracked files. Checked prerequisite availability where needed.

Pulled the latest `main` successfully, now at `d890d8d`. Your untracked `.DS_Store` files were left untouched.


> *Activity:* Saved documentation changes where applicable and exported, verified, committed, and pushed session transcripts with the documented tooling.

Pulled latest `main` successfully. Local files were preserved. Session transcript saved and pushed.

## Prompt 2

can you give me the demo, how to run it?

## Response 2

> *Activity:* Read the README, runbook, and runner; checked local tools, saved logs, and viewer options.

The recorded demo is already on this Mac, so you can view it without Docker or API calls. I also checked the fresh-run commands. The current model is `deepseek-flash`, and the `shared` phase does make model calls despite what the README's phase table says.


> *Activity:* Saved documentation changes where applicable and exported, verified, committed, and pushed session transcripts with the documented tooling.

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

> *Activity:* Saved documentation changes where applicable and exported, verified, committed, and pushed session transcripts with the documented tooling.

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

> *Activity:* Saved documentation changes where applicable and exported, verified, committed, and pushed session transcripts with the documented tooling.

**Only partly. The current demo compares frameworks; it isn't a step-by-step Inspect AI tutorial.** My earlier instructions showed how to run it, not how Inspect works.

The code contains the right ingredients, but a teaching walkthrough should introduce them in order:

1. Define one repair problem as a dataset sample.
2. Create an Inspect `Task`.
3. Configure the solver and shell tool.
4. Run the agent inside a Docker sandbox.
5. Score its repair with fixed tests.
6. Open the evaluation log and explain what happened.

Completed-task recovery can come afterward. The four-framework comparison should be optional context, not the main lesson.

## Prompt 5

can you create a very simple inspect ai tutorial?

## Response 5

> *Activity:* Checked repository status and pulled main, preserving untracked files. Checked prerequisite availability where needed.

I'll make a tiny question-and-answer tutorial with one file and no Docker. It will show how Inspect connects a dataset, model generation, scoring, and the results viewer.


> *Activity:* Created and documented the tutorial; tested real Inspect execution with mock responses and provider initialization without paid requests. Committed and pushed tutorial changes.

The tutorial is written and tested. It covers three questions, scoring, and the log viewer, with a no-key mock run and an optional paid OpenAI run. I verified correct and incorrect answers without making any paid calls.


> *Activity:* Saved documentation changes where applicable and exported, verified, committed, and pushed session transcripts with the documented tooling.

Created and pushed to `main`.

- [Tutorial](docs/inspect-ai-tutorial.md): step-by-step explanation.
- [Example](tutorial/first_eval.py): 22 lines covering questions, model generation, and scoring.

Try it now without an API key or Docker:

```bash
source .venv-tutorial/bin/activate

inspect eval tutorial/first_eval.py \
  --model mockllm/model --log-dir tutorial/mock-logs

inspect view --log-dir tutorial/mock-logs --port 7575
```

Open **http://localhost:7575**. The mock returns dummy answers, so its expected score is zero. The tutorial also explains how to run a real model.

## Prompt 6

did you mock everything?

## Response 6

> *Activity:* Saved documentation changes where applicable and exported, verified, committed, and pushed session transcripts with the documented tooling.

No. **Only the model's replies were mocked during testing.** Inspect's dataset handling, solver execution, scoring, and log creation all ran for real.

I haven't tested a live model call. The tutorial includes the command to use OpenAI with your API key.

## Prompt 7

we can use deepseek key in the terminal. ALSO i need to know isnt inspect ai tool to create a snapshot of environment and then quickly load same environment whenever working on a evaluation?

## Response 7

> *Activity:* Checked repository status and pulled main, preserving untracked files. Checked prerequisite availability where needed.

The DeepSeek key is available. I'll use it for a real run of the three-question tutorial.

Inspect is primarily an evaluation framework. It can recreate isolated environments from Docker images and configuration, but that is different from automatically snapshotting and restoring a running environment.


> *Activity:* Read Inspect sandbox and checkpoint documentation and checked installed checkpoint support. Listed DeepSeek model IDs without exposing credentials, ran the real three-question evaluation with the terminal key, and verified 3/3 correct answers. Updated the tutorial and changelog.

The real DeepSeek run passed all three questions.

I also found an important qualification to my earlier answer: Inspect supports opt-in agent checkpoints. These can restore saved agent state and selected sandbox files into a fresh container, but not process memory or a whole running machine. The tutorial now explains that distinction and includes the DeepSeek command.


> *Activity:* Created and documented the tutorial; tested real Inspect execution with mock responses and provider initialization without paid requests. Committed and pushed tutorial changes.
