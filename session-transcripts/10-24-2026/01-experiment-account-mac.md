---
type: "transcript"
title: "Consolidated experiment account"
description: "Verbatim user prompts and condensed assistant activity from the session that explored all prior work and wrote docs/experiment-report.md."
timestamp: "2026-10-24T10:04:00-04:00"
source: "Claude Code session on mac (default account)"
---

# Consolidated experiment account

## Prompt 1

So, look at this product, I want ideas practical tutorial for Inspect-AI, Like look at /Users/ankitsingh/dev/Inspect-AI/session-transcripts/10-18-2026 and
/Users/ankitsingh/dev/Inspect-AI/session-transcripts/10-18-2026/pi-session-2026-10-18T16-09-38-645Z_01a14fc6-9c55-7c56-89ad-806a065c7a8c.html

## Mid-turn message

I am just looking for one md document that details the experiment but I want you to explore everything we have done so far

## Response

> *Activity:* Scouted the repository and session-transcript folders; decoded the 2.5 MB base64 pi-session HTML export into a plain-text transcript (275 entries, 15 user turns). Read the README, docs bundle (comparison-results, comparison-runbook, inspect-ai-review, inspect-ai-tutorial, index, log), the original inspect-ai-conversation.md, the dated git history (2026-10-04 through 2026-10-18), and the recorded run artifacts. Fanned out three reader agents: a digest of the 2026-10-18 session (framework-value, primitives, reconsidered complementarity, checkpointing answers), a digest of the 2026-10-04 review/explain transcripts, and an inventory of the tutorial, presentation, slides, and original example folders.

Wrote `docs/experiment-report.md` (added to `docs/index.md`, logged in `docs/log.md`, committed as `930d0a9`): a single consolidated account of the four-framework experiment — timeline, motivating question, starting examples and review, comparison design, build and integration problems, measured results (shared pass, live pass, recovery, ~$0.009 cost), findings and the integrated-execution conclusion, 2026-10-11 portability work, the 2026-10-18 teaching arc, the framework conclusions (primitives, reconsidered complementarity, snapshot-vs-checkpoint), a repository map, and known gaps (committed API key in `Inspect_Eg_1` Git history, README shared-phase inaccuracy, orphaned `first_eval.py` mock path, missing failure-path material) plus natural next tutorials. The raw pi-session HTML was committed beside its curated part exports, matching the 2026-10-04 precedent.
