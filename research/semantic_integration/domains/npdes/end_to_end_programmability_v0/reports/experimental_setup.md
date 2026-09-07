# Experimental setup

## MEASURED

- Draft spine: sealed Purpose-First Python Spine Probe T5
- WHEN DISCHARGING: sealed obligation probe Arm B T1 (`ADMIT_DISPOSABLE`, SOURCE_ESTABLISHED)
- pass/fail: sealed obligation probe Arm B T3 (supported; 8 `pass_fail_outcome_reporting` rows). T1 apply completed with 0 binary rows; T2 crashed. T3 is the successful mechanical apply.
- State D: skipped (prior parent/child admission mismatch)
- Model for fresh agents: Composer 2.5
- Consumers frozen after State A; hashes recorded in `frozen/consumer_hashes.json`

## OBSERVED

Sealed T5 / obligation artifacts were hashed before disposable copies. Construction used native sources only inside `states/*/compile/`. Isolated consumers received sqlite + header only.

## HYPOTHESIS

Compiled semantic state can be an ordinary SQL/Python substrate without rereading heterogeneous sources.
