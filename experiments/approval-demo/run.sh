#!/bin/bash
# Approval experiment: the eval that stops and asks.
#
#   ./run.sh            interactive demo - allowlists pass safe commands,
#                       everything else escalates to YOU at the terminal
#                       (requires a TTY and Docker)
#   ./run.sh --record   unattended recording - same allowlists, but escalated
#                       calls are auto-rejected; produces logs/ for the deck
#
# Defaults: deepseek-flash via DeepSeek. Override MODEL/BASE_URL/KEY_VAR as in
# experiments/judge-swap/run.sh (z.ai needs -M responses_api=false, added
# automatically when BASE_URL contains z.ai).
set -euo pipefail
cd "$(dirname "$0")"

MODE="${1:-}"
MODEL="${MODEL:-deepseek-flash}"
BASE_URL="${BASE_URL:-https://api.deepseek.com}"
KEY_VAR="${KEY_VAR:-DEEPSEEK_API_KEY}"
LOG_DIR="${LOG_DIR:-logs}"
MESSAGE_LIMIT="${MESSAGE_LIMIT:-30}"   # the task sets no limit; without one a persistent model loops for hours
INSPECT="${INSPECT:-$(cd ../.. && pwd)/.venv-tutorial/bin/inspect}"
[ -x "$INSPECT" ] || INSPECT=inspect

: "${!KEY_VAR:?export $KEY_VAR first}"

# Docker: use the running daemon, else the repo's dedicated Colima profile
if ! docker info >/dev/null 2>&1; then
  export DOCKER_HOST="unix://$HOME/.colima/inspect-tutorial/docker.sock"
  docker info >/dev/null 2>&1 || { echo "Docker not reachable - start it (colima start --profile inspect-tutorial)"; exit 1; }
fi

EXTRA=()
case "$BASE_URL" in *z.ai*) EXTRA+=(-M responses_api=false);; esac

if [ "$MODE" = "--record" ]; then
  POLICY="approval-record.yaml"
  echo "== Recording run (auto-reject escalation tier) =="
else
  POLICY="approval.yaml"
  echo "== Interactive demo - approve/reject at the prompts =="
fi

mkdir -p "$LOG_DIR"
OPENAI_API_KEY="${!KEY_VAR}" "$INSPECT" eval task.py \
  --approval "$POLICY" \
  --model "openai/$MODEL" --model-base-url "$BASE_URL" ${EXTRA[@]+"${EXTRA[@]}"} \
  --message-limit "$MESSAGE_LIMIT" \
  --log-dir "$LOG_DIR"

L=$(ls -t "$LOG_DIR"/*.eval | head -1)
echo
echo "Log: $L"
echo "Decisions:  ../../.venv-tutorial/bin/python summarize.py \"$L\""
echo "Explore:    \"$INSPECT\" view --log-dir \"$LOG_DIR\" --port 7575"
