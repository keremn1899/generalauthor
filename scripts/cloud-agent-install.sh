#!/usr/bin/env bash
# Idempotent environment bootstrap for Graphauthor development.
#
# Prepares everything the local product needs to run end to end:
#   - uv (installed if the base image does not already provide it)
#   - the Python environment from uv.lock, with all optional extras and dev deps
#   - the frontend's npm dependencies
#   - the default demo graph the product UI opens (data/ is gitignored, so a
#     fresh checkout has no graph until this runs)
#
# Safe to run repeatedly: uv sync and npm ci converge, and the demo graph
# rebuild is deterministic.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

export PATH="$HOME/.local/bin:$PATH"

if ! command -v uv >/dev/null 2>&1; then
  echo "[install] uv not found; installing"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

echo "[install] uv $(uv --version)"

echo "[install] syncing Python environment (all extras + dev)"
uv sync --extra all --extra dev

echo "[install] installing frontend dependencies"
( cd frontend && npm ci )

echo "[install] building the default demo graph"
uv run --extra all python scripts/build_demo_graph.py

echo "[install] done"
