---
type: review
title: Inspect AI advantages and a fair comparison experiment
description: Review of the two local examples, their saved evaluation results, and a proposed comparison with Ragas, DeepEval, and MLflow.
timestamp: 2026-10-04T13:08:05-04:00
---

# Inspect AI advantages and a fair comparison experiment

## Bottom line

The [earlier conversation](../inspect-ai-conversation.md) makes the right distinction. Inspect runs an evaluation procedure, rather than only storing and displaying its results. Its strongest advantage is reducing the code needed for controlled, tool-using agent experiments.

However, these two example directories mostly demonstrate question answering. They do not demonstrate sandboxed agent tasks. For these examples, a small model-calling script with Ragas or DeepEval scoring and MLflow tracking could be sufficient. Inspect does not automatically produce better judgments.

## What the examples actually show

### Inspect_Eg_1

[Eval.py](../Inspect_Eg_1/Eval.py) defines three questions, a chain-of-thought prompt step, model generation, and a text matcher. DeepSeek is called through the OpenAI-compatible provider. Inspect supplies the task runner and logs, but this is a small evaluation that would be straightforward to implement elsewhere.

The saved run scores 2 of 3 answers correct. The missed question asks for a data structure for vector search, but the target is `vector database`. The model answers `HNSW graph`, a defensible answer to the question as written. This is a target/scoring problem, not evidence that the model lacks the knowledge.

The code comment says the scorer checks whether the output contains the target. In the checked upstream source, `match()` defaults to matching at the end, not anywhere in the output. In the saved failure, the model discusses vector databases but finishes with HNSW. The difference matters when interpreting scores.

At review time, this Git-tracked script contained a hardcoded API credential. The user subsequently said they deleted the key. If that means revoking it at the provider, the exposed credential is no longer usable. Deleting it only from the file would not resolve the exposure because Git history retains it. Use an environment variable for any replacement. This review does not reproduce the credential.

### Inpect Eg_2

The [tutorial](../Inpect%20Eg_2/test-an-llm-with-inspect-ai/README.md) demonstrates more reusable evaluation procedures:

- `hello_world.py` checks an exact response.
- `gsm8k.py` maps a dataset to samples, selects seeded few-shot examples, builds prompts, and scores numeric answers.
- `hellaswag.py` supplies multiple-choice questions and a choice scorer.
- `theory_of_mind.py` chains generation with self-critique, then uses model grading.
- `security.py` uses model-graded fact checking. Despite its name, it is a security question-answering task, not an interactive security environment.
- `mathematics.py` implements a custom model-based equivalence scorer.
- `tools.py` registers an addition tool and allows model tool use. Its scorer only checks the final number, so a correct answer does not prove the model used the tool.

The saved logs report successful Hello World checks for GPT-4o-mini and DeepSeek, 86% on 100 theory-of-mind samples, and 94% on only the first 50 GSM8K test samples. These are different tasks and procedures, not a controlled comparison between models or frameworks. No saved logs were found for the other four tasks.

The math scorer needs attention before reuse. Its prompt appends the literal `xw` to Expression 1, uses the full `solution` as its target, and accepts only an exactly lowercased `yes` without trimming whitespace. `get_model()` also defaults to the evaluated model when no separate grader is supplied. Those choices can affect the score independently of the answer's mathematical correctness.

The tutorial pins `inspect_ai==0.3.114`. The cloned upstream snapshot is current `main`, so check API compatibility rather than assuming the tutorial and snapshot behave identically. Also, the README's `python tasks/...` commands do not themselves call evaluations because those scripts only define tasks. Use its `inspect eval ...` commands.

## What Inspect adds beyond these demos

The official source documents facilities for:

- Provisioning separate sandbox instances and starting files for each sample, then cleaning up the environments.
- Running shell/Python tools and multi-turn agents with execution limits.
- Running multiple tasks and models, retrying failures, and reusing completed samples when resuming evaluation sets.
- Applying custom scorers to actions or the resulting environment, and retaining the messages, tool events, and scores needed to diagnose failures.

You still write the task, choose suitable limits, and define what success means. A sandbox setting does not move every custom tool or scorer into a container. Code must use Inspect's sandbox interface for the requested work to run there.

Sources: [sandboxing](https://inspect.aisi.org.uk/sandboxing.html), [ReAct agents](https://inspect.aisi.org.uk/react-agent.html), [evaluation sets](https://inspect.aisi.org.uk/eval-sets.html), and [scorer implementation](../reference/inspect_ai/src/inspect_ai/scorer/_match.py). The exact source revisions are recorded in [reference snapshots](reference-snapshots.md).

## The next tutorial to look for

Find a coding-agent tutorial that gives each sample a broken Python project in a Docker environment, lets an agent inspect and edit files and run commands, then scores the resulting project with fixed tests. That demonstrates what the current examples leave out.

Start with the official [sandboxing guide](https://inspect.aisi.org.uk/sandboxing.html) and [ReAct agent guide](https://inspect.aisi.org.uk/react-agent.html). The local [code execution example](../reference/inspect_ai/examples/code_execution.py) shows the basic sandbox setup, but alone it is too small to demonstrate the advantage.

## Compare the same experiment fairly

Use the same model version, prompts, starting files, tools, permissions, budget, and grading tests. Keep grading tests outside the agent's editable files, and make the scorer run those fixed tests against the final project.

Use two comparison passes:

1. Run one common agent implementation and feed the same outputs and trajectories to each evaluation stack. This tests scoring and reporting without confusing them with differences in agent behavior.
2. Build the complete experiment in each stack. For Inspect, use its runner, sandbox, and custom scorer. For Ragas, DeepEval, and MLflow, use the execution support each selected version actually offers, and record any additional runner or sandbox code required. Do not assume competitors lack a capability without checking their current documentation.

Report test pass rate, token use and cost, how well each system explains failures, what happens after an interrupted run, and the integration code each setup requires. Do not expect identical stochastic model outcomes merely because the settings match.

The hypothesis is that Inspect needs less custom execution code for this agent experiment. A result showing that the other tools cover it with similar effort would weaken that claim. For answer-only or RAG experiments, its advantage may remain small.

## Review scope

Read both directories' Python files, tutorial README and requirements, all five saved evaluation headers, and the three detailed DeepSeek samples. Checked the upstream README, sandboxing and evaluation-set documentation, ReAct guide, code execution example, and matcher implementation. No paid model calls or new evaluations were run. Existing code, logs, and the conversation transcript were left unchanged.
