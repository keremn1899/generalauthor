# Failure analysis

## MEASURED

- protocol_drifts=[]
- fragmented=[]
- unsupported_child_closures=[]
- broader_admissions=[]
- local_underused=[]
- failed_dry_runs=[]
- leakage={}
- mutated_durable=0

## OBSERVED

Do not conflate disposable apply crashes with parent/child protocol drift.
Do not treat a refined parent as independently UNRESOLVED merely because children differ.

## HYPOTHESIS

H1: parent becomes REFINED when heterogeneity is demonstrated. H2: local SOURCE_ESTABLISHED and MODEL_GENERALIZATION can share a relation family with different admission.
