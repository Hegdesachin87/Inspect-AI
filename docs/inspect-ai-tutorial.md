---
type: tutorial
title: Your first Inspect AI evaluation
description: Ask a model three questions, score its answers, and inspect the results with one small Python file.
timestamp: 2026-10-18T12:21:00-04:00
---

# Your first Inspect AI evaluation

Inspect AI runs questions against a model, scores the answers, and saves a record you can inspect. This tutorial teaches that evaluation loop. It does not train a model.

We will ask three capital-city questions. No Docker, coding agent, other evaluation frameworks, or AI judge is needed.

## 1. Set up

These commands are for macOS or Linux. Run them from the repository root with [uv](https://docs.astral.sh/uv/getting-started/installation/) installed:

```bash
uv venv --python 3.12 .venv-tutorial
uv pip install --python .venv-tutorial/bin/python -r tutorial/requirements.txt
source .venv-tutorial/bin/activate
```

This installs Inspect AI, the OpenAI client, and their dependencies, not the four-framework comparison environment.

## 2. Read the evaluation

The complete example is already in [tutorial/first_eval.py](../tutorial/first_eval.py):

```python
from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import match
from inspect_ai.solver import generate, system_message


@task
def capitals():
    return Task(
        dataset=[
            Sample(input="What is the capital of France?", target="Paris"),
            Sample(input="What is the capital of Japan?", target="Tokyo"),
            Sample(input="What is the capital of Italy?", target="Rome"),
        ],
        solver=[
            system_message("Reply with only the city name, without punctuation."),
            generate(),
        ],
        scorer=match(location="exact"),
    )
```

Here is what each part does:

- A `Sample` contains a question in `input` and the expected answer in `target`. The model sees the question, not the target.
- The dataset is our list of three samples.
- The solver describes how to obtain an answer. `system_message()` sets the response format, then `generate()` calls the model once per sample.
- The scorer checks each model answer against its target. `match(location="exact")` compares the whole answer, ignoring case and surrounding whitespace and punctuation. `paris` passes for `Paris`; `The capital is Paris` fails. This is a text check, not a second model call.
- `Task` connects the dataset, solver, and scorer. `@task` makes the function discoverable by the Inspect command.

For each sample, the flow is **question → model answer → score**. Inspect also saves the messages and scores in an evaluation log.

## 3. Run it

For OpenAI, enter your API key without putting it in shell history:

```bash
printf 'OpenAI API key: '
read -r -s OPENAI_API_KEY
export OPENAI_API_KEY
echo
```

If you previously configured DeepSeek or another OpenAI-compatible endpoint, clear that setting before using an OpenAI key:

```bash
unset OPENAI_BASE_URL
```

Run the evaluation:

```bash
inspect eval tutorial/first_eval.py \
  --model openai/gpt-4o-mini \
  --max-tokens 30 \
  --log-dir tutorial/logs
```

This makes three paid model requests on a normal successful run. Provider retries can add requests. The model is selected at the command line, so changing it does not require editing the task.

Inspect displays accuracy. Three correct answers produce `1.0`; two produce about `0.667`. A short, correct answer is required, so extra explanation can lower the score even when the model knows the capital.

### Use DeepSeek instead

If your terminal already has `DEEPSEEK_API_KEY` set, run:

```bash
OPENAI_API_KEY="$DEEPSEEK_API_KEY" inspect eval tutorial/first_eval.py \
  --model openai/deepseek-flash \
  --model-base-url https://api.deepseek.com \
  --max-tokens 128 \
  --log-dir tutorial/logs
```

The `openai/` prefix selects the OpenAI-compatible API client, not OpenAI's service. The explicit base URL sends the requests to DeepSeek. The key assignment applies only to this command and does not replace your terminal's existing OpenAI key.

A real DeepSeek run on 2026-10-18 answered `Paris`, `Tokyo`, and `Rome`, scoring 3/3. This verifies the live evaluation path, not general model ability. The larger output allowance leaves room for this model's reasoning tokens.

### Try it without an API key

Instead of the live command, you can run:

```bash
inspect eval tutorial/first_eval.py \
  --model mockllm/model \
  --log-dir tutorial/mock-logs
```

Inspect's built-in mock model returns dummy text, not capital-city answers, so accuracy should be `0.0`. This checks the evaluation and log-viewing workflow without network requests or API charges. It does not measure a real model.

## 4. Open the results

For a live run:

```bash
inspect view --log-dir tutorial/logs --port 7575
```

For a mock run, use `--log-dir tutorial/mock-logs` instead. Open [localhost:7575](http://localhost:7575), select the evaluation, and open a sample. Look at the question, system instruction, model answer, target, and score. Stop the viewer with `Ctrl+C`.

## 5. Make one change

Add another sample to the dataset:

```python
Sample(input="What is the capital of Germany?", target="Berlin"),
```

Rerun the same evaluation command. Inspect now evaluates four questions and writes a new log. A live rerun makes new paid requests.

You have now defined an Inspect task, run a model, scored its responses, and examined the evidence. These three questions teach the mechanics; they are not a meaningful benchmark of general model ability.

## Does Inspect snapshot an environment?

Inspect is an evaluation framework with optional environment management:

- A Docker image and configuration define a repeatable starting environment. Inspect can start a fresh isolated sandbox for each sample. Prebuilt images avoid rebuilding dependencies, but container startup and sample setup still take time.
- [Agent checkpointing](https://inspect.aisi.org.uk/checkpointing.html) can save registered agent state, selected sandbox filesystem paths, and Inspect's sample state. A retry can restore those into a fresh sandbox and continue. It requires a compatible Inspect version and a checkpoint-aware agent, and must be enabled explicitly.
- A checkpoint is not a full running-machine snapshot. It does not restore arbitrary process memory, running tools, sockets, or external services.

This first tutorial uses neither a sandbox nor checkpoints. The separate [coding-agent comparison runbook](comparison-runbook.md) demonstrates Docker environments and completed-task reuse after interruption. That reuse is different from restoring an unfinished agent from a checkpoint.
