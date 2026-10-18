---
type: presentation
title: Present the Inspect AI coding-repair demo
description: A nine-slide presentation with spoken narration, live terminal commands, and a clearly labeled real-recording fallback.
timestamp: 2026-10-18T12:38:16-04:00
---

# Present the Inspect AI coding-repair demo

Use the [browser slide deck](inspect-ai-slides.html) with the narration below. It follows the six tutorial steps across nine slides. Allow about ten minutes, plus questions and model latency.

The runnable code and detailed explanations are in the [tutorial](inspect-ai-tutorial.md). This demo makes real DeepSeek calls, runs shell commands in Docker, and grades the repaired file with fixed tests. The fallback is a saved real run, not mocked output.

## Before the audience arrives

Use two terminals and a browser. Keep the slides and source files ready before sharing your screen.

### Terminal A: prepare the evaluation

On this Mac:

```bash
cd /Users/ankitsingh/dev/Inspect-AI
source .venv-tutorial/bin/activate
```

For a new checkout without that environment, run these first:

```bash
uv venv --python 3.12 .venv-tutorial
uv pip install --python .venv-tutorial/bin/python -r tutorial/requirements.txt
```

If the environment already exists but dependencies have not been installed, run only the second command. Then activate it.

Start the dedicated Docker VM and keep the previous global context:

```bash
previous_context=$(docker context show)
colima start --profile inspect-tutorial --cpu 2 --memory 2 --disk 8
docker context use "$previous_context"
export DOCKER_HOST="unix://$HOME/.colima/inspect-tutorial/docker.sock"

docker info --format '{{.ServerVersion}}'
docker compose -f tutorial/compose.yaml pull
```

This setup is for this Mac's Colima installation. With Docker Desktop or Linux Docker, use your working Docker daemon instead. Download packages and images before presenting.

If `DEEPSEEK_API_KEY` is not already set, enter it now, off-screen:

```bash
printf 'DeepSeek API key: '
read -r -s DEEPSEEK_API_KEY
export DEEPSEEK_API_KEY
echo
```

Never print the key or display an environment dump. The live command uses the variable name, not a literal credential.

Open the slides and source files:

```bash
open docs/inspect-ai-slides.html
open -t tutorial/repair.py tutorial/compose.yaml tutorial/fixed_tests.py
```

You can use your usual code editor instead of `open -t`. In the slide deck, use the arrow keys or navigation buttons. The full-screen button enlarges the deck; browser Print can save all slides as a PDF.

### Terminal B: start the live-results viewer

Use port 7576 so this does not collide with the earlier recorded-run viewer on 7575:

```bash
cd /Users/ankitsingh/dev/Inspect-AI
source .venv-tutorial/bin/activate
mkdir -p tutorial/repair-logs
inspect view --log-dir tutorial/repair-logs --port 7576
```

Leave this terminal running and open [localhost:7576](http://localhost:7576). If 7576 is already occupied, stop your previous viewer or choose another port and use that address.

The viewer can show previous rehearsals. During the demo, select the new log identified by the filename printed in Terminal A. Do not present an old result as the new live run.

## Slide 1. Evaluate a real coding repair

**Show:** The opening slide.

**Say:**

> Today I'm going to evaluate a coding agent using Inspect AI. I'll give DeepSeek a broken Python function and a shell tool. It will inspect and edit the file inside Docker. Then fixed Python tests will decide whether the repair worked.
>
> DeepSeek is the model doing the repair. Inspect runs the evaluation around it. We'll look at the commands, the saved source, and the test result, rather than taking the model's word for it.

## Slide 2. Define the problem and starting file

**Show:** The broken function on the slide. Then open `tutorial/repair.py` and point to `STARTING_CODE` and the `Sample` inside `repair()`.

**Say:**

> This function is called sum-even, but it sums everything. With one, two, three, and four, it returns ten. The correct answer is six.
>
> In Inspect, a Sample is one evaluation problem. Here its input describes the repair requirements, and its files field supplies the broken project.py. We also require empty inputs and negative integers to work, without changing the input list.
>
> The file path is inside the container. The agent has to change that file. Writing a correct function in its final chat message would not be enough.

**Point out:** There is one dataset sample. The five grading tests later are not five dataset samples.

## Slide 3. Connect the experiment

**Show:** The Task slide, then point to `@task`, `return Task(...)`, `dataset`, `solver`, `sandbox`, and `scorer` in the source.

**Say:**

> The Task brings the experiment together. The dataset says what problem to attempt. The solver says how the model should work. The sandbox says where commands execute. The scorer says how we judge the result.
>
> The task decorator lets Inspect discover this function from the command line. I'll choose DeepSeek when I run it, so the problem definition isn't tied to that model.
>
> We still author the requirements, environment configuration, and tests. Inspect supplies the evaluation runner, tool dispatch, sandbox lifecycle, and logs.

## Slide 4. Let the model inspect, edit, and check

**Show:** The solver list in `tutorial/repair.py`.

**Say:**

> The solver starts with an instruction to edit the actual file and check the repair. Next we expose Inspect's built-in bash tool, bound to the agent's default container.
>
> Generate runs the conversation loop. When DeepSeek requests a shell command, Inspect executes it and sends the output back. The model can inspect the code, edit it, and run another check before finishing.
>
> We haven't written our own API loop or tool dispatcher. Each shell command has a thirty-second timeout, and this small task allows at most six model turns.

## Slide 5. Keep repair and grading separate

**Show:** The two-container slide. Open `tutorial/compose.yaml` and point to `default`, `grader`, the pinned `image`, `network_mode`, and `tmpfs`.

**Say:**

> There are two containers. The default container holds the broken file and is the only environment the model's shell tool can access. The grader has a separate filesystem and no network connection to it.
>
> Once the agent finishes, the scorer copies the final source and our fixed tests into the grader. The model can write its own checks, but it cannot edit the fixed grading test file through its shell tool.
>
> The model API client runs on the host. These containers do not receive the API key or mount my project folder. Only the shell work runs inside Docker.

**Do not claim:** This is a full-machine snapshot, a guarantee of instant startup, or a hardened adversarial grader. It recreates a clean starting environment from a pinned image and configuration. Checkpoint restoration is not enabled in this demo.

## Slide 6. Run the evaluation

**Show:** Terminal A. Run this command block:

```bash
RUN="tutorial/repair-logs/demo-$(date +%Y%m%d-%H%M%S)"

OPENAI_API_KEY="$DEEPSEEK_API_KEY" inspect eval tutorial/repair.py \
  --model openai/deepseek-flash \
  --model-base-url https://api.deepseek.com \
  --log-dir "$RUN"
```

**Say before pressing Enter:**

> This is the live evaluation. The openai prefix selects an OpenAI-compatible API client, but the base URL sends the requests to DeepSeek. The key comes from my terminal environment. This run makes real paid model requests.

**Say while it runs:**

> Inspect is creating the sandboxes, placing the broken file in the agent workspace, and running the model and tool loop. When the agent finishes, Inspect will call our scorer and write the evaluation log.

**When it finishes:** Read the actual displayed result. Do not promise success or say that it used four calls before inspecting this run. Note the new log filename for the viewer.

If it fails or the API is unavailable, use the labeled fallback below. Do not keep rerunning paid evaluations just to fill presentation time.

## Slide 7. Test the saved file, not the claim

**Show:** `tutorial/fixed_tests.py`, then the `repair_tests()` scorer in `tutorial/repair.py`.

**Say:**

> These are ordinary Python unit tests that we wrote before the run. They check mixed values, empty input, all-odd input, negative numbers and zero, and whether the input list stays unchanged.
>
> The scorer reads the final file and executes these tests in the separate grader. All five must pass for this sample to score one. If any fails, it scores zero. There is no second model judging the answer.
>
> The model may print that its own checks passed. That's useful feedback for the agent, but it isn't the official grade. Our scorer's fixed-test output is what determines the result.

**If useful:** The checked-in [Docker control outputs](../tutorial/recorded/controls.json) show that the original code failed four tests and a reference repair passed all five. Label these as prior control runs, not work performed by today's agent.

## Slide 8. Show what actually happened

**Show:** [The live viewer](http://localhost:7576). Select the evaluation matching Terminal A's new log filename, then sample `sum-even`. Refresh the browser if the new log is not listed yet.

Walk through these in order:

1. The input requirements and initial system instruction.
2. The model's bash calls and their returned outputs.
3. The command that rewrote `project.py`.
4. Any checks the agent ran itself.
5. The `repair_tests` score, its saved source, and its fixed-test explanation.

**Say:**

> Now we can follow the run rather than guessing from its final answer. Here are the commands it requested. Here is what the shell returned. Here is the source the scorer actually read.
>
> This last result is from our fixed tests in the grader, after the agent finished. That separates the agent's claim from the evaluation's evidence.

**If the live score is 1.0, say:**

> All five fixed tests passed, so this one sample scored one. That means this repair passed our checks. It doesn't establish that the model can repair arbitrary programs.

**If the live score is 0.0, say:**

> At least one fixed test failed, so this sample scored zero. The log shows which requirement was missed. A failed repair is still a recorded evaluation result.

The slide's four generations, four shell calls, and five passing tests describe the real saved run from 2026-10-18. They are not predictions about the live run. Show the saved run only with that label.

## Slide 9. A repeatable experiment with evidence

**Show:** The closing slide.

**Say:**

> We defined one problem, connected it to an Inspect Task, gave the model a shell tool, ran it in Docker, graded the repaired file, and inspected the log.
>
> We wrote the problem and tests. Inspect ran the experiment and recorded what happened. A rerun starts from the same broken file in a fresh sandbox, rather than inheriting the previous agent's edits.
>
> That's the workflow this example teaches. This is one small repair, not a coding leaderboard or a demonstration of checkpoint recovery.

## Recorded-run fallback

If the live provider or Docker run fails, say this explicitly:

> The live run couldn't complete, so I'm switching to a saved real DeepSeek run from October eighteenth. This is its original Inspect log, not today's result and not mocked model output.

In an available terminal:

```bash
cd /Users/ankitsingh/dev/Inspect-AI
source .venv-tutorial/bin/activate
inspect view --log-dir tutorial/recorded --port 7577
```

Open [localhost:7577](http://localhost:7577), select `repair`, then `sum-even`. This viewer needs neither Docker nor another API call.

The saved run shows the broken example returning ten, a file edit, the agent's own checks, then five passing fixed grading tests. It contains four model generations and four shell calls. Its first generation requested two shell commands.

## After the demo

Stop viewers with `Ctrl+C`. If you used the dedicated VM and are finished with it:

```bash
colima stop --profile inspect-tutorial
```
