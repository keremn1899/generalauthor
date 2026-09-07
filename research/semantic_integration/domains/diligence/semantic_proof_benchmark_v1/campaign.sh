#!/usr/bin/env bash
set -euo pipefail
cd "/home/kerem/Desktop/Personal Projects/generalauthor"
export PYTHONPATH=.
LOG="research/semantic_integration/domains/diligence/semantic_proof_benchmark_v1/campaign.log"
{
  echo "RESUME $(date -Iseconds)"
  for s in a2_critic a3_entailment a4_proof_obligation a5_pairwise a6_multistep; do
    echo "STRATEGY $s $(date -Iseconds)"
    python3 -m research.semantic_integration.domains.diligence.semantic_proof_benchmark_v1.runner --strategy "$s" --replications 5 --workers 3
  done
  python3 -m research.semantic_integration.domains.diligence.semantic_proof_benchmark_v1.report
  echo "DONE $(date -Iseconds)"
} >>"$LOG" 2>&1
