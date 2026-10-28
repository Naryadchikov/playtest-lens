#!/usr/bin/env bash
# Runs Claude Code headless against an open model on a Modal Shared Endpoint.
# The proxy token is read from the macOS Keychain (service MODAL_PROXY_TOKEN) for this process only.
# Usage: tools/run-modal-agent.sh deepseek|glm|kimi "prompt" [extra claude flags...]
# Run it from the repo or from the author's worktree. deepseek writes code; glm and kimi review.
set -euo pipefail
set +x

case "${1:-}" in
  deepseek) name="deepseek-1017"; model="deepseek-ai/DeepSeek-V4.1-Flash-1017" ;;
  glm)      name="glm-53";        model="zai-org/GLM-5.3" ;;
  kimi)     name="kimi-k3";       model="moonshotai/Kimi-K3" ;;
  *) echo "Usage: $0 deepseek|glm|kimi \"prompt\" [claude flags...]" >&2; exit 2 ;;
esac
shift

if ! token="$(security find-generic-password -a "$USER" -s MODAL_PROXY_TOKEN -w 2>/dev/null)"; then
  echo "MODAL_PROXY_TOKEN is not in the Keychain (service MODAL_PROXY_TOKEN). Stop and tell Sasha." >&2
  exit 1
fi

prompt="$1"; shift
env -u ANTHROPIC_API_KEY \
  ANTHROPIC_BASE_URL="https://naryadchikov--ep-${name}-server.us-west.modal.direct" \
  ANTHROPIC_AUTH_TOKEN="$token" \
  ANTHROPIC_MODEL="$model" \
  ANTHROPIC_DEFAULT_OPUS_MODEL="$model" \
  ANTHROPIC_DEFAULT_SONNET_MODEL="$model" \
  ANTHROPIC_DEFAULT_HAIKU_MODEL="$model" \
  ANTHROPIC_DEFAULT_FABLE_MODEL="$model" \
  CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 \
  claude -p "$prompt" --max-turns 30 "$@"
