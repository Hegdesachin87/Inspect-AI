---
type: "transcript"
title: "Inspect AI review and comparison plan"
description: "Verbatim user prompts and assistant responses from an agent session, with tool calls and thinking condensed."
timestamp: "2026-10-04T17:08:05+00:00"
source: "2026-10-04T17-03-03-202Z_01a107de-7a22-7361-8de1-682301f1aee5.jsonl"
---

# Inspect AI review and comparison plan

Source: 2026-10-04T17-03-03-202Z_01a107de-7a22-7361-8de1-682301f1aee5.jsonl (pi) · Session: 01a107de-7a22-7361-8de1-682301f1aee5

Prompts and responses are copied verbatim. Quoted *Activity* lines are editorial summaries of tool calls and model thinking, not source text.

## Prompt 1

review the two directories and tell me /Users/ankitsingh/dev/Inspect-AI/inspect-ai-conversation.md what is the advantage of inspect ai . also clone the inspect ai github repo

## Response 1

> **Activity (draft; summarize):**
> - read: /Users/ankitsingh/.pi/agent/skills/unslop/SKILL.md
> - bash: `pwd; ls -la; find . -name AGENTS.md -not -path '*/node_modules/*' -not -path '*/.git/*'; git status --short; git remote -v`
> - bash: `find 'Inpect Eg_2' Inspect_Eg_1 -maxdepth 4 -type f; date '+%Y-%m-%dT%H:%M:%S%z'; printenv | grep '^PI_' | cut -d= -f1; ls -la /Users/ankitsingh/dev/AGENTS.md 2>/dev/null` **(failed)**
> - read: /Users/ankitsingh/dev/Inspect-AI/inspect-ai-conversation.md
> - thinking: (encrypted; no visible text)

I’ll review both example directories and the conversation file, then check the official Inspect AI source. I’ll place a source snapshot under `reference/inspect_ai` and explain what Inspect adds beyond scoring and dashboards.


> **Activity (draft; summarize):**
> - read: /Users/ankitsingh/dev/Inspect-AI/Inspect_Eg_1/Eval.py
> - read: /Users/ankitsingh/dev/Inspect-AI/Inpect Eg_2/test-an-llm-with-inspect-ai/README.md
> - read: /Users/ankitsingh/dev/Inspect-AI/Inpect Eg_2/test-an-llm-with-inspect-ai/requirements.txt
> - bash: `for f in 'Inpect Eg_2/test-an-llm-with-inspect-ai/tasks/'*.py; do printf '\n%s\n' "$f"; done; git log -3 --oneline; printf '\nSession: %s\n' "$PI_SESSION_FILE"; git ls-files`
> - thinking: (encrypted; no visible text)
> - read: /Users/ankitsingh/dev/Inspect-AI/Inpect Eg_2/test-an-llm-with-inspect-ai/tasks/hello_world.py
> - read: /Users/ankitsingh/dev/Inspect-AI/Inpect Eg_2/test-an-llm-with-inspect-ai/tasks/gsm8k.py
> - read: /Users/ankitsingh/dev/Inspect-AI/Inpect Eg_2/test-an-llm-with-inspect-ai/tasks/hellaswag.py
> - read: /Users/ankitsingh/dev/Inspect-AI/Inpect Eg_2/test-an-llm-with-inspect-ai/tasks/mathematics.py
> - read: /Users/ankitsingh/dev/Inspect-AI/Inpect Eg_2/test-an-llm-with-inspect-ai/tasks/security.py
> - read: /Users/ankitsingh/dev/Inspect-AI/Inpect Eg_2/test-an-llm-with-inspect-ai/tasks/theory_of_mind.py
> - read: /Users/ankitsingh/dev/Inspect-AI/Inpect Eg_2/test-an-llm-with-inspect-ai/tasks/tools.py
> - bash: `tmp=$(mktemp -d /tmp/inspect-ai-source.XXXXXX) && printf '%s\n' "$tmp" > /tmp/inspect-ai-review-clone-path && git clone --depth 1 https://github.com/UKGovernmentBEIS/inspect_ai.git "$tmp/inspect_ai" && git -C "$tmp/inspect_ai" remote -v &&…`
> - thinking: **Inspecting code and logs** I need to look over the clone to ensure everything is working. I'll check the README file and focus on core components like sandbox, eval_set, and scorer match. I also need to review the logs; I want to create …
> - bash: `python3 - <<'PY' from pathlib import Path import zipfile,json for p in sorted(Path('.').glob('*/**/*.eval')): print('\nLOG',p) try: with zipfile.ZipFile(p) as z: print('entries',z.namelist()[:12]) for name in ('header.json','summary.json')…`
> - thinking: (encrypted; no visible text)

The examples show reusable evaluation steps and scoring, but neither tests agents in a sandbox. Inspect’s bigger advantage is therefore mostly absent from these demos.

I also found a hardcoded API credential in `Inspect_Eg_1/Eval.py`, which is tracked by Git. Revoke or rotate it and load its replacement from the environment.


> **Activity (draft; summarize):**
> - read: /tmp/inspect-ai-source.Y11r5F/inspect_ai/README.md
> - read: /tmp/inspect-ai-source.Y11r5F/inspect_ai/docs/sandboxing.qmd
> - read: /tmp/inspect-ai-source.Y11r5F/inspect_ai/docs/eval-sets.qmd
> - read: /tmp/inspect-ai-source.Y11r5F/inspect_ai/docs/react-agent.qmd
> - read: /tmp/inspect-ai-source.Y11r5F/inspect_ai/src/inspect_ai/scorer/_match.py
> - read: /Users/ankitsingh/.pi/agent/skills/verbatim-session-transcript/SKILL.md
> - bash: `python3 - <<'PY' from pathlib import Path import json,zipfile p=next(Path('Inspect_Eg_1/logs').glob('*.eval')) with zipfile.ZipFile(p) as z: h=json.loads(z.read('header.json'));print('version',h['eval'].get('inspect_version'));print('plan'…`

## Prompt 2

next, i will try to find another tutorial as a way to use inspect ai to show the advantage. Like let's have ragas and DeepEval and MLflow with same experiment and show differences

## Response 2

> **Activity (draft; summarize):**
> - thinking: **Considering cloning options** I need to find the best way to respond to the user's request about cloning a repository. I’m thinking about whether to initially complete a clone snapshot and provide clear documentation, especially with the…

A sandboxed coding-agent tutorial would make the difference clearer: give an agent a broken Python project, let it edit files and run commands, then grade it with tests.

For a fair comparison, separate what each tool provides from the runner, sandbox, and retry code you add yourself. Keep the model, prompts, starting files, tool permissions, budget, and grading identical.


> **Activity (draft; summarize):**
> - bash: `source_dir=$(python3 -c "from pathlib import Path; print(Path('/tmp/inspect-ai-review-clone-path').read_text().strip()+'/inspect_ai')") du -sh "$source_dir"; git -C "$source_dir" submodule status; rg -n 'version|requires-python' "$source_d…`
> - thinking: **Considering submodule cloning** I'm thinking about whether I could clone the submodule as a snapshot to capture the revision path and include the frontend. It might not be necessary, but a complete clone could be nice. However, since the…
> - read: /tmp/inspect-ai-source.Y11r5F/inspect_ai/examples/code_execution.py
> - thinking: **Reviewing source control requirements** I'm working on finding a stable source for the historical version pinned at 0.3.114. I need to confirm the details by fetching the raw request without executing the tool. Using git, I want to check…
> - bash: `source_dir=$(python3 -c "from pathlib import Path; print(Path('/tmp/inspect-ai-review-clone-path').read_text().strip()+'/inspect_ai')") git -C "$source_dir" submodule update --init --depth 1 && git -C "$source_dir" submodule status`
> - bash: `python3 - <<'PY' from pathlib import Path import shutil,subprocess prepared=Path('/tmp/inspect-ai-review-clone-path').read_text().strip() src=Path(prepared)/'inspect_ai' dest=Path('reference/inspect_ai') if dest.exists(): raise SystemExit(…`
> - write: /Users/ankitsingh/dev/Inspect-AI/docs/inspect-ai-review.md

## Prompt 3

yeah i deleted that key

## Response 3

> **Activity (draft; summarize):**
> - thinking: (encrypted; no visible text)

If you revoked it in DeepSeek, that resolves the exposure. If you only deleted it from the file, revoke it too, since Git history can retain it.

I’ve saved the review and a comparison plan. The main thing to look for in the next tutorial is sandboxed agent execution with test-based grading, rather than another answer-scoring demo.


> **Activity (draft; summarize):**
> - write: /Users/ankitsingh/dev/Inspect-AI/docs/reference-snapshots.md
> - write: /Users/ankitsingh/dev/Inspect-AI/docs/index.md
> - write: /Users/ankitsingh/dev/Inspect-AI/docs/log.md
> - write: /Users/ankitsingh/dev/Inspect-AI/session-transcripts/README.md
> - thinking: **Inspecting documentation exposure** I need to adjust the document exposure because the user mentioned a deleted key. I should keep a note to review any changes since the status might still need inspection. It’s essential to have an actua…
> - bash: `date '+%Y-%m-%dT%H:%M:%S%z'; git status --short; python3 /Users/ankitsingh/.pi/agent/skills/verbatim-session-transcript/scripts/transcript.py draft "$PI_SESSION_FILE" .sessions/transcript-draft.md --title 'Inspect AI review and comparison …`
