# External context — Probe A (not scoring)

What is already known:
- Entity matching / record linkage: decide whether two references denote the same real-world entity.
- Selective classification and abstention: refuse to commit when evidence is insufficient (Chow's reject option; later selective prediction).
- Risk–coverage evaluation: plot error on committed predictions against the fraction committed.
- Evidence entailment / NLI and proof verification: decompose a claim into supporting facts and check license.

What differs:
- The unit is a bounded packet plus a relation contract, not a full corpus or similarity features.
- UNRESOLVED is a successful open-world output, not a timeout.
- Unsupported closure (committing SAME/DISTINCT on oracle-UNRESOLVED) is the primary hazard, not pairwise F1 alone.
- A cue verifier or critic may only downgrade; it may not search extra sources.

What we borrow:
- Separate risk from coverage rather than collapsing into accuracy.
- Report abstention vs false-commitment, and whether a second-stage critic catches false commitments at the cost of killing true SAME.
