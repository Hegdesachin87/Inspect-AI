---
type: "transcript"
title: "Small Inspect experiments scoping and guide"
description: "Continuation of the 10-24 experiment-account session: chose the next direction, swept official Inspect docs and examples with three readers, and wrote docs/small-inspect-experiments.md."
timestamp: "2026-10-25T00:35:00-04:00"
source: "Claude Code session on mac (default account)"
---

# Small Inspect experiments scoping and guide

Continues the 2026-10-24 session (session-transcripts/10-24-2026/01-experiment-account-mac.md).

## Prompts

1. "so what is the experiment we are aiming for now?" — replied with the untested claim from the 10-18 conclusions: the composed pipeline (Inspect execution + external metric scorer + MLflow sink), with the alternative of quantifying recovery reuse.
2. "yeah but for one end-to-end combined integration, what will we integerate?" — detailed the three components and two seams: Inspect stays the framework; DeepEval demoted to a metric library called inside an Inspect scorer; MLflow demoted to a passive sink fed from the .eval log.
3. "but what experiment?" — stated the experimental question (does composition preserve resume and evidence integrity, and does the added metric add signal), two arms, four measurements, outcomes declared in advance.
4. "do you understand, what will be the objective forr that end-to-end combined integeration?" — objective: show a team already on DeepEval+MLflow can add Inspect as the execution layer without replacing anything, and measure cost and preservation; architectural, evaluative, pedagogical sub-objectives.
5. "no we should try to do eval on something real, like make that experiment?" — proposed real benchmarks from the inspect_evals catalog (267 evals checked): SWE-bench Verified subset with deepseek-chat vs deepseek-reasoner recommended, Terminal-Bench as lighter alternative.
6. "anything else that is not doing evaluation on real benchmark?" — offered non-benchmark families: build-your-own eval from real PRs, red-team your own harness, ablation evals, applied evals on owned data, model-behavior probes.
7. "i mean give me something small" — proposed the 10-run stability eval of tutorial/repair.py (cents, ~30-60 min, fills the missing failure-log gap).
8. "maybe research inspect ai tutorials or documentation, find that?" — swept the official material with three parallel readers (tutorial.qmd + orientation; 17 advanced doc pages; all 48 bundled examples), filtered for DeepSeek+Docker runnability, and produced a ranked top-10 of small hands-on items.
9. "ok create an md file of top 5. and then flesh out those experiments in same with real links. Commit and push and then give me github link" — verified commands empirically (`inspect score` syntax validated end-to-end with mockllm on inspect-ai 0.3.276), wrote docs/small-inspect-experiments.md, updated index and changelog, committed and pushed.

## Response gist (final)

The guide covers: (1) re-score one unscored log with includes / model_graded_fact self- and cross-grading; (2) the approval demo with allowlist approvers escalating to human; (3) the two-call deepseek-chat vs deepseek-reasoner tool-use probe; (4) cache A/B with inspect cache list; (5) theory_of_mind as the smallest LLM-judge eval. Each with validated commands, official-docs links, repo-relative example links, measurements, expected findings, and honest limits. Pushed as docs/small-inspect-experiments.md.
