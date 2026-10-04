# Inspect AI, Ragas, DeepEval, and MLflow — conversation transcript

Date: October 4, 2026

User prompts and assistant responses are preserved below. Citation widgets have been converted to ordinary Markdown links.

## User — prompt 1

isnt inspect ai just a fancy storage of telemetry and presentation layer. cant the other software such ragas or DeepEval do same? What about ml flow?

## Assistant — progress message

I’ll check how Inspect AI, Ragas, DeepEval, and MLflow divide evaluation execution, scoring, and result tracking.

## Assistant — response 1

**There’s substantial overlap, but Inspect AI does more than store telemetry and display it.** Its core is an **evaluation runner**: a task combines a dataset, a solver that executes the model or agent, and a scorer. It also supplies tools, sandboxed execution, and controls for running evaluations. The logs and viewer expose what happened during that execution. [Inspect documentation](https://inspect.aisi.org.uk/)

Your intuition is right for simpler evaluations: **feeding questions to an application, scoring answers, and comparing runs doesn’t inherently require Inspect.**

| Tool | Main emphasis | How it overlaps |
|---|---|---|
| **Inspect AI** | Defining and executing model/agent experiments | Runs anything from single responses to agents interacting with sandboxed environments; scores and records results. |
| **Ragas** | Application evaluation and experimentation | Retrieval and answer metrics, plus agent/tool metrics, test-data generation, datasets, and result tracking. |
| **DeepEval** | Testing LLM applications | End-to-end, trajectory, and component evaluation, with metrics and CI/CD testing. |
| **MLflow** | Tracking, tracing, evaluation, and lifecycle management | Runs evaluations and manages results; can use Ragas and DeepEval metrics as scorers. |

These are emphases, rather than exclusive capabilities. [Inspect](https://inspect.aisi.org.uk/), [Ragas](https://docs.ragas.io/en/stable/), [DeepEval](https://deepeval.com/docs/getting-started), [MLflow Ragas integration](https://www.mlflow.org/docs/latest/genai/eval-monitor/scorers/third-party/ragas/), [MLflow DeepEval integration](https://www.mlflow.org/docs/latest/genai/eval-monitor/scorers/third-party/deepeval/), [MLflow evaluation](https://mlflow.org/docs/latest/genai/eval-monitor/)

The distinction becomes clearer with two examples:

- **“Did my RAG chatbot answer correctly and use retrieved evidence?”** Ragas or DeepEval can cover the evaluation, and MLflow can provide tracing and experiment tracking.
- **“Can this agent fix a repository inside an isolated environment, using specified tools and limits, and pass executable checks?”** Inspect supplies more of the experimental execution machinery. Its documentation includes agents using shell tools inside Docker sandboxes. [Ragas](https://docs.ragas.io/en/stable/), [MLflow DeepEval integration](https://www.mlflow.org/docs/latest/genai/eval-monitor/scorers/third-party/deepeval/), [Inspect](https://inspect.aisi.org.uk/)

**My assessment:** if you already have an application runner and primarily need scoring, tracing, and comparisons, Inspect may add little value. MLflow plus Ragas or DeepEval can be sufficient. Inspect becomes more compelling when you want it to own the evaluation procedure and environment—especially for agent benchmarks.

You could build equivalent procedures around the other tools. The practical question is **how much execution infrastructure you would have to implement and maintain yourself**, rather than whether they can produce the same score or dashboard.

## User — prompt 2

whats the edge

## Assistant — response 2

**Inspect’s edge is controlling the experiment—not better scoring or prettier dashboards.**

For complex agent evaluations, it gives you a reusable way to define:

- **Environment:** files, tools, and sandbox the agent receives.
- **Execution:** how the agent runs and what limits apply.
- **Success:** grading against answers, actions, or resulting environment state.
- **Evidence:** the transcript and results needed to investigate failures. [Inspect documentation](https://inspect.aisi.org.uk/)

For example: “Give each model the same broken codebase, tools, and budget; let it attempt a repair; then run tests.” Inspect provides much of the machinery around that experiment.

**If your application already handles execution and you just need to score its outputs, the edge is small.** Ragas/DeepEval plus MLflow can cover that workflow, and MLflow integrates both libraries’ scorers. [MLflow Ragas integration](https://www.mlflow.org/docs/latest/genai/eval-monitor/scorers/third-party/ragas/), [MLflow DeepEval integration](https://www.mlflow.org/docs/latest/genai/eval-monitor/scorers/third-party/deepeval/)

My take: **Inspect saves engineering effort for controlled agent benchmarks. It isn’t inherently a better judge of answer quality.**

## User — prompt 3

download the whole intraction so far prompt and response style including links in form of an md file

## Assistant — progress message

I’ll create a Markdown transcript of your prompts and my responses, with source links included. I’m using the Library skill to make the file available for download.
