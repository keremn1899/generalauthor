# Retrieval trace

## MEASURED

Arm B mean documents touched=6.291666666666667 mean retained snippets=7.791666666666667

| trial | obligation | docs touched | queries | retained | budget exception |
| --- | --- | --- | --- | --- | --- |
| T1 | nodi_c | 7 | 17 | 7 | False |
| T1 | nodi_9 | 5 | 23 | 7 | False |
| T1 | when_discharging | 4 | 10 | 7 | False |
| T1 | geometric_mean | 4 | 12 | 8 | False |
| T1 | pass_fail | 2 | 6 | 8 | False |
| T1 | empty_numeric_limit | 7 | 10 | 8 | False |
| T1 | document_authority | 13 | 7 | 8 | True |
| T1 | monitoring_frequency | 8 | 11 | 8 | False |
| T2 | nodi_c | 8 | 17 | 8 | False |
| T2 | nodi_9 | 8 | 19 | 8 | False |
| T2 | when_discharging | 4 | 7 | 7 | False |
| T2 | geometric_mean | 3 | 8 | 8 | False |
| T2 | pass_fail | 2 | 6 | 8 | False |
| T2 | empty_numeric_limit | 6 | 9 | 8 | False |
| T2 | document_authority | 11 | 15 | 8 | False |
| T2 | monitoring_frequency | 8 | 18 | 8 | False |
| T3 | nodi_c | 6 | 11 | 7 | False |
| T3 | nodi_9 | 7 | 18 | 8 | False |
| T3 | when_discharging | 5 | 8 | 8 | False |
| T3 | geometric_mean | 3 | 9 | 8 | False |
| T3 | pass_fail | 3 | 7 | 8 | False |
| T3 | empty_numeric_limit | 7 | 10 | 8 | False |
| T3 | document_authority | 13 | 15 | 8 | False |
| T3 | monitoring_frequency | 7 | 19 | 8 | False |

## OBSERVED

Soft budget is 5 documents / 8 snippets. Broad nomination would show most of the 12 document files opened per obligation.

## HYPOTHESIS

Obligation-first retrieval stays local to the question.
