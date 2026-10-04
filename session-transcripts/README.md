# Session transcripts

Save each session under `session-transcripts/MM-DD-YYYY/NN-topic-machine.md`, using `mac` or `windows`. Number sessions in order within each date folder. Later saves of the same session use `-part-2`, `-part-3`, and so on. Helper transcripts belong in a sibling `NN-topic-subagents/` directory.

Save a Pi session draft with:

```bash
python3 /Users/ankitsingh/.pi/agent/skills/verbatim-session-transcript/scripts/transcript.py draft "$PI_SESSION_FILE" .sessions/transcript-draft.md --title "Session topic"
```

Summarize tool and thinking activity, retain prompt and response text, then check the final transcript with the script's `check` command. Commit and push only the transcript paths.
