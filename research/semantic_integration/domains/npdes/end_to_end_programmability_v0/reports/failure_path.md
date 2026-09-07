# Failure path

## MEASURED

{
  "FAILED_CANDIDATE_PRESERVES_ACCEPTED": true,
  "FAILED_CANDIDATE_PRESERVES_APPLICATION_OUTPUT": true,
  "before_world_sha256": "f98f735aa16cf9dbe7283a5ef4d2f819092b224c6ed58a2d836d9e8f7643ebd4",
  "after_world_sha256": "f98f735aa16cf9dbe7283a5ef4d2f819092b224c6ed58a2d836d9e8f7643ebd4",
  "before_csv_sha256": "aac71014bbd9a94719113e1d6cb8ff7b89c5929bcbb58881537521c10187d9c4",
  "after_csv_sha256": "aac71014bbd9a94719113e1d6cb8ff7b89c5929bcbb58881537521c10187d9c4",
  "compile_returncode": 1,
  "compile_ok_expected_false": true
}

Reopen: {
  "state_a": {
    "REOPEN_WITHOUT_RECONSTRUCTION": true,
    "original_sha256": "b4c1f17acf702a4290fac18002a2e38c05d6f3e1da3c5631b5aab67692709b42",
    "reopen_sha256": "b4c1f17acf702a4290fac18002a2e38c05d6f3e1da3c5631b5aab67692709b42"
  },
  "state_b": {
    "REOPEN_WITHOUT_RECONSTRUCTION": true,
    "original_sha256": "f36fa13c8fd69a9f092493675c0726f5a871f2ec2e355e86357050972ce0622d",
    "reopen_sha256": "f36fa13c8fd69a9f092493675c0726f5a871f2ec2e355e86357050972ce0622d"
  },
  "state_c": {
    "REOPEN_WITHOUT_RECONSTRUCTION": true,
    "original_sha256": "aac71014bbd9a94719113e1d6cb8ff7b89c5929bcbb58881537521c10187d9c4",
    "reopen_sha256": "aac71014bbd9a94719113e1d6cb8ff7b89c5929bcbb58881537521c10187d9c4"
  }
}

## OBSERVED

Invalid construction.py in a disposable directory did not write the accepted World or application CSV. Reopening each isolated consumer reproduced identical CSV hashes.

## HYPOTHESIS

Failed candidates can fail closed if they never share a write path with accepted/.
