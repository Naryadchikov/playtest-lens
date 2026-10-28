#!/usr/bin/env bash
# Runs an analyzer script with BASETEN_API_KEY read from the macOS Keychain (service BASETEN_API_KEY).
# The key exists only in this process and the Python it execs; never in a profile or the caller's shell.
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

cd "$root"
exec "$python" "$@"
