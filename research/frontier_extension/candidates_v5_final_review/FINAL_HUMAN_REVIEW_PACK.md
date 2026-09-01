# Final human-review pack — prompt-corrected frontier candidates

## Gate status

| Gate | Status |
| --- | --- |
| 14/14 structural, oracle, parity, and feasibility admissions | PASS |
| Prompt ↔ oracle ↔ grader output consistency | PASS |
| Per-named-output cardinality ≤6 | PASS |
| FX04 forbidden-predicate neutral-oracle fixture | PASS |
| Participant/model execution | NOT RUN |

The frozen answer-cardinality rule is **per named answer set**, not the union
of all named outputs. The aggregate total is therefore descriptive only.

## Dose-family output alignment

| Family | Cases | Requested named outputs | Status |
| --- | --- | --- | --- |
| Depth / closure | FX01 → FX02 → FX03 | `affected_services` | PASS |
| Intermediate reuse | FX14 → FX06 → FX07 | `affected_services, affected_deployments, uncovered_services, boundary_sensitive_services` | PASS |
| Cyclic topology | FX08 → FX09 | `affected_services, owners, affected_deployments` | PASS |
| Negative / absence | FX10 → FX11 | `affected_services, affected_deployments` | PASS |

## Case review cards

### FX01

Prompt: For task:fx01-cutover, which production services remain affected by retiring package:fx01-legacy? Return the affected production service IDs.

Named outputs/cardinalities: `affected_services`: 6.

Structure: depth 3; closure 18; branching 3; required predicates 2; cycle `False`; absence `False`; oracle `bounded_closure`.

Accepted witness: `service:fx01-00` in `affected_services`.

### FX02

Prompt: For task:fx02-cutover, which production services remain affected by retiring package:fx02-legacy? Return the affected production service IDs.

Named outputs/cardinalities: `affected_services`: 5.

Structure: depth 5; closure 64; branching 5; required predicates 3; cycle `False`; absence `False`; oracle `bounded_closure`.

Accepted witness: `service:fx02-00` in `affected_services`.

### FX03

Prompt: For task:fx03-cutover, which production services remain affected by retiring package:fx03-legacy? Return the affected production service IDs.

Named outputs/cardinalities: `affected_services`: 6.

Structure: depth 8; closure 240; branching 8; required predicates 3; cycle `False`; absence `False`; oracle `bounded_closure`.

Accepted witness: `service:fx03-00` in `affected_services`.

### FX04

Prompt: For task:fx04-cutover, return production service IDs that require review because their approved migration is affected by package:fx04-legacy and does not cross the deprecated integration boundary.

Named outputs/cardinalities: `approved_route_services`: 3.

Structure: depth 5; closure 72; branching 5; required predicates 4; cycle `False`; absence `False`; oracle `constrained_reachability`.

Accepted witness: `service:fx04-00`. Near miss rejected only for `crosses_deprecated`: `service:fx04-01`.

### FX05

Prompt: For task:fx05-cutover, a deployment is eligible only when its service implements a module that depends on package:fx05-legacy, the package is covered by the migration, and that migration targets the deployment. Return eligible production service IDs and eligible deployment IDs.

Named outputs/cardinalities: `eligible_deployments`: 1, `eligible_services`: 6.

Structure: depth 8; closure 200; branching 7; required predicates 5; cycle `False`; absence `False`; oracle `ordered_sequence`.

Accepted witness: `deployment:fx05-production` in `eligible_deployments`.

### FX06

Prompt: For task:fx06-cutover, which production services remain affected by retiring package:fx06-legacy? Return: affected production service IDs; their affected deployment IDs; affected service IDs lacking required integration verification; and affected service IDs that cross a relevant boundary.

Named outputs/cardinalities: `affected_deployments`: 1, `affected_services`: 5, `boundary_sensitive_services`: 5, `uncovered_services`: 2.

Structure: depth 5; closure 92; branching 5; required predicates 4; cycle `False`; absence `False`; oracle `bounded_closure`.

Accepted witness: `deployment:fx06-production` in `affected_deployments`.

### FX07

Prompt: For task:fx07-cutover, which production services remain affected by retiring package:fx07-legacy? Return: affected production service IDs; their affected deployment IDs; affected service IDs lacking required integration verification; and affected service IDs that cross a relevant boundary.

Named outputs/cardinalities: `affected_deployments`: 1, `affected_services`: 6, `boundary_sensitive_services`: 6, `uncovered_services`: 3.

Structure: depth 8; closure 300; branching 8; required predicates 5; cycle `False`; absence `False`; oracle `bounded_closure`.

Accepted witness: `deployment:fx07-production` in `affected_deployments`.

### FX08

Prompt: For task:fx08-cutover, which production services remain affected by retiring package:fx08-legacy? Return: affected production service IDs; owner team IDs that must approve; and affected deployment IDs.

Named outputs/cardinalities: `affected_deployments`: 1, `affected_services`: 5, `owners`: 2.

Structure: depth 5; closure 82; branching 5; required predicates 4; cycle `True`; absence `False`; oracle `bounded_closure`.

Accepted witness: `deployment:fx08-production` in `affected_deployments`.

### FX09

Prompt: For task:fx09-cutover, which production services remain affected by retiring package:fx09-legacy? Return: affected production service IDs; owner team IDs that must approve; and affected deployment IDs.

Named outputs/cardinalities: `affected_deployments`: 1, `affected_services`: 6, `owners`: 2.

Structure: depth 8; closure 250; branching 7; required predicates 4; cycle `True`; absence `False`; oracle `bounded_closure`.

Accepted witness: `deployment:fx09-production` in `affected_deployments`.

### FX10

Prompt: For task:fx10-cutover, which production services remain affected by retiring package:fx10-legacy? Treat the supplied frozen task view as complete for the declared production dependency scope relevant to this question. Return affected production service IDs and affected deployment IDs.

Named outputs/cardinalities: `affected_deployments`: 0, `affected_services`: 0.

Structure: depth 5; closure 102; branching 5; required predicates 4; cycle `False`; absence `True`; oracle `bounded_closure`.

Closed universe: `package:fx10-legacy`, incoming `depends_on`, max depth 5, visited nodes 103. No accepted witness is appropriate for an absence judgment.

### FX11

Prompt: For task:fx11-cutover, which production services remain affected by retiring package:fx11-legacy? Treat the supplied frozen task view as complete for the declared production dependency scope relevant to this question. Return affected production service IDs and affected deployment IDs.

Named outputs/cardinalities: `affected_deployments`: 0, `affected_services`: 0.

Structure: depth 8; closure 280; branching 8; required predicates 5; cycle `False`; absence `True`; oracle `bounded_closure`.

Closed universe: `package:fx11-legacy`, incoming `depends_on`, max depth 8, visited nodes 281. No accepted witness is appropriate for an absence judgment.

### FX12

Prompt: For task:fx12-cutover, which production services remain affected by retiring package:fx12-legacy? Return: affected production service IDs that both cross a regulated boundary and lack required integration verification; and their affected deployment IDs.

Named outputs/cardinalities: `affected_deployments`: 1, `boundary_unverified_services`: 3.

Structure: depth 6; closure 150; branching 7; required predicates 5; cycle `False`; absence `False`; oracle `qualified_set_composition`.

Accepted witness: `deployment:fx12-production` in `affected_deployments`.

### FX13

Prompt: For task:fx13-cutover, which production services remain affected by retiring package:fx13-legacy? Return: affected production service IDs; eligible deployment IDs; affected service IDs lacking required integration verification; and affected service IDs crossing a regulated boundary.

Named outputs/cardinalities: `affected_services`: 6, `eligible_deployments`: 1, `regulated_services`: 6, `uncovered_services`: 3.

Structure: depth 7; closure 220; branching 7; required predicates 5; cycle `False`; absence `False`; oracle `constrained_reachability`.

Accepted witness: `service:fx13-00` in `affected_services`.

### FX14

Prompt: For task:fx14-cutover, which production services remain affected by retiring package:fx14-legacy? Return: affected production service IDs; their affected deployment IDs; affected service IDs lacking required integration verification; and affected service IDs that cross a relevant boundary.

Named outputs/cardinalities: `affected_deployments`: 1, `affected_services`: 6, `boundary_sensitive_services`: 0, `uncovered_services`: 3.

Structure: depth 3; closure 20; branching 3; required predicates 3; cycle `False`; absence `False`; oracle `bounded_closure`.

Accepted witness: `deployment:fx14-production` in `affected_deployments`.


## Integrity material for final freeze

| Case | Canonical facts SHA-256 | Oracle SHA-256 | SQL projection SHA-256 | Graph projection SHA-256 |
| --- | --- | --- | --- | --- |
| FX01 | `926130a7bf7ddd69c92c7e3158d2cdf6f30f166a9868c72fa5c24b43b856437c` | `c074c5c94e13b883c3da6d8fed771fca654cfc94a26bb685017fa96683626e36` | `066e4c5108ad73aba98151a3cd6fcc38bd63e6d6a211b9d62e79e9c8e4f5d699` | `245595080a764917cedcf34b732933ba0a8c55a59ff0f4bf15e258bfed553d49` |
| FX02 | `412ba3df87bf4e1d3a3ffd35036a8c1bcadbe450b2e990ff1f029e3ccd2148eb` | `c93d8915cfdf42b94b6d34e8638f2c647f34887d285b362390f52af16012d2ae` | `1591dca06c8e4781ba7ce202b365292c50f1144e1c18767b0e07783aaa4ee7e2` | `add477aa7161505e2b9b540bfe4e89c37c90c4a47907f8e951271d3d2f6a3989` |
| FX03 | `c0e714ac4bc8d0682f82a4b405aaa7f33925627fe04f198b7d6d63722749d01d` | `fdbea32da4facad60e770fd012027530034f9fd4f0fb1cca816261865add23cd` | `6216b03b5eb0d0ad97e335b78323cc6133ece0cf09282d419037fdc49cfa4d2e` | `15ceca207d6d2a7f8675c6067ebbe2c9964487791e76026891b945f73b374634` |
| FX04 | `bf2d64de13ade131965999894dc4c29d2fed4cebd80799597c9e68bb305c04b0` | `88a1ed87ab9521c1b175d9da3578913726977ea6823a4fe30b0a91e4e7b0f507` | `91e2f7b1f85dfb21cab09e8040e5176e7a6e58132e783b5c8794e87753b10251` | `44ba4d832923523c0ecdeb4864e8d6a32bc3deab7bd22d48f8f6ef77266ab8a4` |
| FX05 | `094c040a56b06fec4fdc64b4074bf350e7de75f6ed07f6aa676a6a6993b00e9c` | `61f28b54b25c5b51da2eb57b643340118e7b38acedd05f86240cc4a950ee792e` | `ccb0799dac766c0ce365831556dbf514d95817484d6da309ca769f9f88fe6101` | `c821a183ffa4748cc224493b6674999dc068ab053e26467d33ea22c3f7555baf` |
| FX06 | `4d2b1ef0de510bf38eff147729485677b70020b1354e8a2f5096e5f3cfe369ba` | `80cf93107ac8f1ba319d3759ed3bc22f0ba318336534737214b91bae6303ed23` | `856efbf869ccad4169b9ddfaf0a017e1ad343832774208def08137a46aba064b` | `614afc49f29d04c9e633781856911e7246e53f6594cf94adcdf36ac4b7a46075` |
| FX07 | `d94050142df38165c73a1d50229f3b6525ac9d0f9b440394376ba4d221362782` | `13186ad8701e05d9a6478ea52aeb149553f0530c70ecc6f3d2984e0b5c7e7504` | `9fd2b1dd2fcdc6b2300e7f6b2634cb60d1dcf5cc144f9db8eb3e3b7e20621b17` | `4b41eeee365651677123853ad7330a7f4d87887fc73cf71496d0f34a59691a2e` |
| FX08 | `0c1c7ccdfc27bd13f9c00373b56bb7f55c3b787b23ec483105485cc9562f2f1b` | `2f4572d005183e2509e848f5b0671fc59f255803a727d97906c0c2ed97be3cf7` | `1305e09b96aa0ff44958d3316874f709b1689d95fb9deef5b5fa86e5313a362c` | `81f4466c5b9907f2068d396f40ba19f8b88439bbc6b08e5a8207483d73cbb08b` |
| FX09 | `d239910d4ef51dba7d58539849db0ed823652287f5e9c3ad8cc02e2112650e13` | `a740f253a17fc7da1bdb0c1f932d7c9d667f065052a1ba98926179a0a1abf735` | `46463e97f09f7904e72a48c9bb3e60bf85c1b2b86c7cecfd58f0c294aad61895` | `5ee1eff5d848c01ae6f0c2ac04c02f44dcd13f6207fca9bc5947e2d190bea1e2` |
| FX10 | `18894dde7ff0f9018f1cafa61083d090891376c57ef42bce2ed75148b519dcef` | `6b267aba2319f876d083ca5959bdf2c5e97072b4c7e73669fe40455474842441` | `156a7fac5a50ea68f8fd8514bebec2017301fabc9ced582cb2e521be4a314594` | `e25b9aa670d7a71c27f16e1789d6cff653745d400e6ff03ab719fb100cb67327` |
| FX11 | `3daf551b6796eb5cfc4fbdc734637220f27fd98ace6d7fa23b373c9eb9f4407c` | `0a49b0a2f6119f6af00cad5a652d77ac1deb611e55128fd3d8bb4ad7b97a8d12` | `693570317b142af2cd4bb8649ca31928af98ec72e413fda6159bd64cf16a6084` | `da422cb3989d86f8d5ba86f30a047425144dfe0e3b6404fa6b6f92aedbc00422` |
| FX12 | `b84105ea7031ff1128f9a134707c7473f9447a2728e538c3ee2d43af5c782606` | `d7f370c9918b9522a0bda1caea8ec8d3e32b7952e1784b85d34404116723bfc3` | `10b48cce2202dc12f290929883c3668a7951c85eae9a4600ee35eca436eac23d` | `0d9ba7ea162e2742a0e8582510d76dca41cdb9286c8c08ce451b0fdfb5ce478d` |
| FX13 | `752b6d208f5baa18722a27f89573cd6014ae7e44d2d343b81f7f05bc2ab4bae3` | `b8ce0d57d854e7a6715b6cdb70b4678cb3f9812fc79c8ccedc8dcc7a7fc6a955` | `35631623074ec25e9dfaf30eca083f4a19ddc374a5cd82f497c79445e960500d` | `a4ed3a13f246057125f0832bb4fc1dced122e295ba2c746ae59113c16bdc36ab` |
| FX14 | `bc596a15aded3cabe9842f90d7aa280a3755d9ef37a60eabfbdc9fe2344bdeb4` | `81f5ddfd914cfc8be93fc9bd47dec2ba3ac9365739e8d1b9a9f3b609d4f87208` | `a670d5b8ed9d8e8ee16713631850496c1c3f3df418adba2d7b6b133d97ab7105` | `2500a82b202ba100dea801cf81994fb593d9222f9c06ead4c866ecb8de71bfc4` |

No participant execution is authorized by this pack. On final approval, add
these hashes plus participant-prompt hashes, treatment/adapter hashes,
environment, and fixed case/arm order to the campaign manifest before any
participant workspace is created.
