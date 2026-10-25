---
type: "transcript"
title: "Judge-swap experiment executed"
description: "Continuation: ran experiment 1 live — z.ai balance failure diagnosed, DeepSeek fallback, 100-sample recorded run, self-contained experiments/judge-swap folder with slide deck."
timestamp: "2026-10-25T01:38:00-04:00"
source: "Claude Code session on mac (default account)"
---

# Judge-swap experiment executed

Continues session-transcripts/10-25-2026/01-small-experiments-mac.md.

## Prompt

"Ok get started on number 1? z.ai glm 5.3 key is in terminal" — then mid-turn: "make sure the code for that experiment is in a separate folder." / "also in that separate folder include a powerpoint that explains the tutorial." / "commit and push when done"

## What happened

> *Activity:* Probed the environment (found ZAI_API_KEY), listed z.ai models via the /models endpoint, and launched arm 0 with glm-5.3 — the run hung 40+ minutes retrying.

Diagnosed the hang: z.ai returns error 1113 ("Insufficient balance") on every model, and Inspect retried it indefinitely. Killed the run; probed five GLM models — all 1113. Fell back to the DeepSeek key in the same terminal (models: deepseek-flash, deepseek-v4-pro), matching the guide's documented default.

Built experiments/judge-swap/ (per the mid-turn instruction): task.py (self-contained copy of the official theory-of-mind example), run.sh (arm 0 unscored generation + three scoring arms; parameterized MODEL/BASE_URL/KEY_VAR; resolves the repo's .venv-tutorial inspect binary; skips redundant judge arms), summarize.py (judge matrix from the log), make_slides.py + judge-swap.pptx (nine-slide deck; results slide built from a results.json dump of the log), README.md, and the recorded log under logs/.

Debugged along the way: Inspect 0.3.276's openai provider calling /responses against z.ai (fixed with -M responses_api=false); `${JUDGE_OLD:-default}` swallowing an intentionally-empty override; macOS unzip unable to read zstd-compressed .eval members (read via Python 3.14 / inspect's API instead); summarize.py fixes for list-style scores and integer sample ids. Scaled from 5 to 20 to 100 samples after the smaller runs showed unanimous agreement.

## Result

100 samples, deepseek-flash evaluated; includes 1.00 (spurious: target noun leaks via story echo, matcher matches substrings anywhere), self-grade 0.94, cross-grade (v4-pro) 0.94 with identical verdicts on every sample — no self-grading leniency; the six contested samples adjudicated by reading transcripts: the model's final ANSWER line was wrong and both judges were right. Docs updated (guide link + z.ai note, changelog). Committed and pushed with the deck, results, and transcript.
