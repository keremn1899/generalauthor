# Neutral oracle specification

The evaluator uses named `derive` expressions over directed canonical facts. Its operations are `resolve`, `traverse`, `reverse_reachable`, `sequence`, `union`, `intersection`, `difference`, and `path_targets`. Inputs and outputs are sets of stable IDs; direction, predicate filters, maximum depth, endpoint kinds, multiple named outputs, and intermediate reuse are explicit. This is an oracle-only language: it is neither SQL nor Graphauthor syntax. `research/abstraction_frontier/test_oracle.py` deterministically exercises every operation.
