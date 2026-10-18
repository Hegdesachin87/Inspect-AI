---
type: tutorial
title: Repair one Python function with Inspect AI
description: Run a real DeepSeek coding agent in Docker, grade its repair with fixed tests, and read the Inspect evaluation log.
timestamp: 2026-10-18T12:31:00-04:00
---

# Repair one Python function with Inspect AI

This tutorial runs a real coding agent. DeepSeek inspects and edits a broken Python file inside Docker. Inspect runs the conversation and shell tool, grades the final file with fixed tests in a separate container, and records what happened. Nothing in this tutorial uses a mock model or replayed model responses.

The runnable example is [tutorial/repair.py](../tutorial/repair.py). The accompanying files are [compose.yaml](../tutorial/compose.yaml) and [fixed_tests.py](../tutorial/fixed_tests.py). The snippets below explain those files; you do not need to assemble them yourself.

## Before you start

You need Python 3.12, [uv](https://docs.astral.sh/uv/getting-started/installation/), Docker with Docker Compose, and a DeepSeek API key. These shell commands are for macOS or Linux and run from the repository root:

```bash
uv venv --python 3.12 .venv-tutorial
uv pip install --python .venv-tutorial/bin/python -r tutorial/requirements.txt
source .venv-tutorial/bin/activate
```

If `.venv-tutorial` already exists, skip its creation and install the requirements before activating it. You do not need the four-framework comparison environment.

## 1. Define one repair problem as a dataset sample

The starting file deliberately sums every number:

```python
STARTING_CODE = "def sum_even(numbers):\n    return sum(numbers)\n"
```

For `[1, 2, 3, 4]`, it returns `10`. We want `6`, the sum of the even numbers only.

In `repair.py`, the dataset contains one `Sample`. Its `input` asks the agent to fix the function, handle empty lists and negative integers, and leave the input unchanged. Its `files` field supplies the broken file:

```python
files={"/workspace/project.py": STARTING_CODE}
```

Inspect places that file in the agent's sandbox before the solver runs. `/workspace/project.py` is a container path, not a file in your checkout. The model must edit this file; an explanation in its final chat reply is not a repair.

There is no answer string in `target`. Our scorer will execute tests against the saved code instead of comparing the model's final message with a reference answer.

## 2. Create an Inspect Task

Open the `repair()` function in [repair.py](../tutorial/repair.py). The `@task` decorator makes it discoverable by `inspect eval`. It returns a `Task` connecting:

- The one-sample dataset and its starting file.
- The solver that instructs the model and runs its tool calls.
- The Docker sandbox configuration.
- The fixed-test scorer.

The model is selected at the command line, not hardcoded in the task. `GenerateConfig` allows up to 1,024 output tokens per generation, one provider retry, and a 60-second request timeout. The task permits at most six model turns. These bound this small paid demonstration; a rerun makes new requests.

## 3. Configure the solver and shell tool

The task's solver is:

```python
solver=[
    system_message(
        "You are fixing a Python function. Edit the actual file, not just "
        "your final reply. Work in /workspace and check your repair."
    ),
    use_tools(bash(timeout=30, sandbox="default")),
    generate(),
]
```

`system_message()` tells the agent how to work. `use_tools()` exposes Inspect's built-in `bash` tool, bound to the `default` container. Each command has a 30-second timeout.

`generate()` handles the model/tool loop. Inspect sends the conversation to DeepSeek, executes requested shell commands, and returns their output to the model. This continues until the model finishes or the task reaches its turn limit. You do not write your own API or tool-dispatch loop.

## 4. Run the agent inside a Docker sandbox

The task selects its sandbox with:

```python
sandbox=("docker", str(HERE / "compose.yaml"))
```

The Compose file defines two containers from the same pinned Python image:

- `default` is the agent workspace. This is the only container its shell tool can use.
- `grader` is a separate workspace for the final source and fixed tests.

They have separate temporary filesystems, no network, no host mounts, a read-only root filesystem, and a non-root user. The API client runs on the host; API keys are not passed into these containers. Only shell work runs inside Docker, not the entire Inspect evaluation process.

### Start Docker

If Docker Desktop or a Linux Docker daemon is already working, use that daemon and skip the Colima commands. On this Mac, use a dedicated Colima profile and restore the previous global Docker context:

```bash
previous_context=$(docker context show)
colima start --profile inspect-tutorial --cpu 2 --memory 2 --disk 8
docker context use "$previous_context"
export DOCKER_HOST="unix://$HOME/.colima/inspect-tutorial/docker.sock"
```

Pull the image specified by the tutorial:

```bash
docker compose -f tutorial/compose.yaml pull
```

### Supply the key and run

If `DEEPSEEK_API_KEY` is already set in this terminal, use it. Otherwise enter it without putting its value in shell history:

```bash
printf 'DeepSeek API key: '
read -r -s DEEPSEEK_API_KEY
export DEEPSEEK_API_KEY
echo
```

Run the actual evaluation:

```bash
OPENAI_API_KEY="$DEEPSEEK_API_KEY" inspect eval tutorial/repair.py \
  --model openai/deepseek-flash \
  --model-base-url https://api.deepseek.com \
  --log-dir tutorial/repair-logs
```

The `openai/` prefix selects the OpenAI-compatible API client. The base URL routes requests to DeepSeek. The temporary key assignment does not replace your terminal's existing OpenAI key.

This makes paid requests and executes the generated repair inside Docker. Inspect creates the sandboxes, seeds the broken file, runs the agent, scores its final code, writes a `.eval` log, and removes the containers. The recorded run passed; future model behavior can differ.

## 5. Score the repair with fixed tests

The `repair_tests()` scorer runs after the solver finishes:

1. Read the final `/workspace/project.py` from the agent container.
2. Copy that source into `grader`.
3. Write the fixed, project-authored tests into `grader`, not the agent workspace.
4. Execute `python -B -m unittest -v fixed_tests` there.
5. Return `CORRECT` only when the test process exits successfully, otherwise `INCORRECT`.

The five tests cover mixed values, an empty list, all-odd values, negative numbers and zero, and preserving the input list. No LLM judges the repair. The agent can write its own checks, but those do not determine the final score.

`Score.answer` stores the actual repaired source. `Score.explanation` stores the fixed-test output. The `accuracy()` metric reports `1.0` if this one sample passes every test, or `0.0` otherwise. It is not the fraction of individual tests passed.

We also ran the fixed tests directly in the grading container: the original source failed four of five tests, and a reference repair passed all five. The outputs are saved in [controls.json](../tutorial/recorded/controls.json). These are real Docker executions, not mocked results.

This is a cooperative repair exercise. Separate containers keep the agent from changing the fixed test file, but the tests and repaired code share a Python process during grading. This is not a hardened anti-cheating system.

## 6. Open the evaluation log and explain what happened

For the evaluation you just ran:

```bash
inspect view --log-dir tutorial/repair-logs --port 7575
```

Open [localhost:7575](http://localhost:7575), select `repair`, and open sample `sum-even`. Stop the viewer with `Ctrl+C`.

### Read the real recorded run

A real DeepSeek + Docker log is also checked into [tutorial/recorded/](../tutorial/recorded/2026-10-18T16-28-58-00-00_repair_a86dcXpoiTkLyrq3QpfcTd.eval). To view it without rerunning the model or starting Docker:

```bash
inspect view --log-dir tutorial/recorded --port 7575
```

In that run on 2026-10-18:

1. The agent read `project.py` and checked the broken function. The shell returned `sum_even([1,2,3,4]) = 10`.
2. The agent rewrote the file to sum only even integers. The actual generated implementation is visible in the tool call and the scorer's answer.
3. The agent ran its own checks for empty inputs, negative numbers, and input preservation.
4. The model finished after four generations and four shell tool calls. Its first generation requested two shell commands.
5. The scorer then read the saved source and ran the five fixed tests in `grader`. All five passed, giving this sample accuracy `1.0`.

When presenting, distinguish the agent's own "ALL TESTS PASSED" tool output from the scorer's independent fixed-test results. Expand the `repair_tests` score to see the latter. The recorded result demonstrates one successful repair, not general coding ability.

## What happens when you rerun?

Inspect creates fresh sandboxes and seeds the same broken file again. The pinned image and configuration reproduce the starting environment; cached images avoid downloading dependencies again. It does not reuse the previous agent's edited file or its answers, and startup still takes time.

This tutorial does not enable agent checkpointing. Restoring an unfinished agent and selected sandbox files requires separate checkpoint configuration and a compatible agent. See [Inspect's checkpointing documentation](https://inspect.aisi.org.uk/checkpointing.html). Recreating a clean starting environment is different from resuming a checkpoint.

When finished on this Mac, stop the dedicated VM:

```bash
colima stop --profile inspect-tutorial
```
