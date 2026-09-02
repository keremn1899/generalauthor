#!/bin/bash
set -euo pipefail
cd "/home/kerem/Desktop/Personal Projects/generalauthor"
exec uv run --extra all python "research/semantic_integration/domains/diligence/constructor_v2/resume.py"
