# ADR: Constructor v3.1.1 ABI materializability invariant

FOUNDATIONAL: kernel unchanged. TaskView hash remains identical (`7704e551b50cacb9`).

COMPILER_INVARIANT: `SATISFIED(f) => f in Normalize(W)` for every required consumer semantic field or relation f. `SATISFIED` is a realizability guarantee, not merely a declaration guarantee.

SINGLE_SOURCE_OF_TRUTH: ABI completeness and normalization share the same materialization semantics. `check_abi()` directly verifies that required canonical relations and fields are materialized by `normalize_world()`.

DIAGNOSTIC_STATUS_MODEL: Status is `SATISFIED`, `UNSATISFIED` (with reasons `NO_BINDING` or `NOT_MATERIALIZABLE`), or `AMBIGUOUS`.

FAILURE_BEHAVIOR: Declared bindings that cannot be mechanically materialized from World produce `UNSATISFIED: NOT_MATERIALIZABLE` and fail closed to `INCOMPLETE_PURPOSE` before projection.
