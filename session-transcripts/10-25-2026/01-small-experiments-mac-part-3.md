---
type: "transcript"
title: "Approval experiment executed and diagnosed"
description: "Continuation: built experiments/approval-demo, diagnosed an unbounded agent loop (2,868 messages, 112M tokens) via inspect ctl, bounded it with --message-limit, recorded the run, and produced the deck."
timestamp: "2026-10-25T15:20:00-04:00"
source: "Claude Code session on mac (default account)"
---

# Approval experiment executed and diagnosed

Continues session-transcripts/10-25-2026/01-small-experiments-mac-part-2.md.

## Prompt

"Now work on experiment number 2 and do the same for it" — then mid-turn: "well figure out why experiment 2 not working?"

## What happened

Built experiments/approval-demo: task.py (official approval example copied from the reference snapshot), approval.yaml (human escalation tier) and approval-record.yaml (auto decision: reject for unattended recording), run.sh with both modes, summarize.py, make_slides.py. Started the Colima inspect-tutorial profile for Docker. Fixed a macOS bash 3.2 empty-array-under-set-u failure in run.sh. First recording attempt: sample 1 completed with a full approval chain, sample 2 stalled ~70 minutes. Diagnosis via `inspect ctl sample list`: the task's react() sets no message limit, and the model retried rejected calls unbounded — 2,868 messages, 1,433 turns, 112,207,634 tokens. Killed the run, added `--message-limit 30` to run.sh, and reran: both samples completed in minutes.

## Result

Recorded run (deepseek-flash, message limit 30): 8 approved (all allowlisted ls/echo/print/math.factorial), 18 rejected (touch, mkdir, cp, ln, rm --help, import os/shutil/tempfile variants, dangerous characters && and >). The agent's adaptations are visible in the chain. In the recorded policy submit is also rejected, so the agent ends at the limit — the interactive demo adds the human judgment of approving the final submit. One unexplained quirk recorded: a submit call handled by python_allowlist. Deck generated (approval-demo.pptx) from results.json. Docs guide + changelog updated; committed and pushed.
