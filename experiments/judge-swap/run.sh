#!/bin/bash
# Judge-swap experiment: same outputs, different judges.
#
# Arm 0 generates the agent transcripts ONCE with --no-score, then three
# scorings are appended to the same log without any re-generation:
#   1. includes          - deterministic string matcher, no model calls
#   2. self-grade        - the evaluated model grades its own answers
#   3. cross-grade (x2)  - two other models grade the same answers
#
# Defaults target z.ai's OpenAI-compatible endpoint (chat-completions only,
# hence -M responses_api=false). Override the variables for DeepSeek or others:
#   MODEL=glm-5.3 JUDGE_FLASH=glm-5.3-flash JUDGE_OLD=glm-4.7 \
#   BASE_URL=https://api.z.ai/api/paas/v4/ ./run.sh
set -euo pipefail
cd "$(dirname "$0")"
INSPECT="${INSPECT:-$(cd ../.. && pwd)/.venv-tutorial/bin/inspect}"
[ -x "$INSPECT" ] || INSPECT=inspect

MODEL="${MODEL:-glm-5.3}"
JUDGE_FLASH="${JUDGE_FLASH:-glm-5.3-flash}"
JUDGE_OLD="${JUDGE_OLD-}"   # unset -> empty; set-but-empty stays (skips the arm)
BASE_URL="${BASE_URL:-https://api.z.ai/api/paas/v4/}"
KEY_VAR="${KEY_VAR:-ZAI_API_KEY}"        # or OPENAI_API_KEY (DeepSeek)
LIMIT="${LIMIT:-5}"
LOG_DIR="${LOG_DIR:-logs}"
PROVIDER_ARGS=(--model "openai/$MODEL" --model-base-url "$BASE_URL" -M responses_api=false)

: "${!KEY_VAR:?export $KEY_VAR first}"

mkdir -p "$LOG_DIR"

echo "== Arm 0: generate unscored ($MODEL, $LIMIT samples) =="
OPENAI_API_KEY="${!KEY_VAR}" "$INSPECT" eval task.py "${PROVIDER_ARGS[@]}" \
  --limit "$LIMIT" --no-score --log-dir "$LOG_DIR"

LOG=$(ls -t "$LOG_DIR"/*.eval | head -1)
echo "Unscored log: $LOG"

score () {  # score <label> [extra args...]
  local label="$1"; shift
  echo "== Scoring: $label =="
  OPENAI_API_KEY="${!KEY_VAR}" "$INSPECT" score "$LOG" --action append --overwrite "$@"
}

echo "== Judge 1: includes (deterministic, free) =="
OPENAI_API_KEY="${!KEY_VAR}" "$INSPECT" score "$LOG" --scorer includes --action append --overwrite

score "self-grade ($MODEL)" \
  --scorer model_graded_fact --model "openai/$MODEL" --model-base-url "$BASE_URL" -M responses_api=false

score "cross-grade ($JUDGE_FLASH)" \
  --scorer model_graded_fact --model "openai/$JUDGE_FLASH" --model-base-url "$BASE_URL" -M responses_api=false

if [ -n "$JUDGE_OLD" ] && [ "$JUDGE_OLD" != "$JUDGE_FLASH" ] && [ "$JUDGE_OLD" != "$MODEL" ]; then
  score "cross-grade ($JUDGE_OLD)" \
    --scorer model_graded_fact --model "openai/$JUDGE_OLD" --model-base-url "$BASE_URL" -M responses_api=false
fi

echo
echo "All scorings appended to: $LOG"
echo "Summarize:  python summarize.py \"$LOG\""
echo "Explore:    "$INSPECT" view --log-dir \"$LOG_DIR\" --port 7575"
