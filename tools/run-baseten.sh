#!/usr/bin/env bash
# Runs an analyzer script with BASETEN_API_KEY read from the macOS Keychain (service BASETEN_API_KEY).
# META_API_KEY is added when it is in the Keychain too: the open-weights check still transcribes each clip with Muse Voice Transcribe.
# The keys exist only in this process and the Python it execs; never in a profile or the caller's shell.
# Usage: tools/run-baseten.sh analyzer/spark_test.py [args...]
set -euo pipefail
set +x

root="$(cd "$(dirname "$0")/.." && pwd)"
python="$root/.venv/bin/python"
[ -x "$python" ] || { echo "No .venv: run 'python3 -m venv .venv' in $root first." >&2; exit 1; }

if ! BASETEN_API_KEY="$(security find-generic-password -a "$USER" -s BASETEN_API_KEY -w 2>/dev/null)"; then
  echo "BASETEN_API_KEY is not in the Keychain (service BASETEN_API_KEY). Stop and tell Sasha." >&2
  exit 1
fi
export BASETEN_API_KEY
if META_API_KEY="$(security find-generic-password -a "$USER" -s META_API_KEY -w 2>/dev/null)"; then
  export META_API_KEY
fi

cd "$root"
exec "$python" "$@"
