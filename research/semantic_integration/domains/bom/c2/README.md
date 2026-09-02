# Authorized C2 campaign

Manifest: `authorized.json`

This authorizes only the two frozen `acceptable_replacement` packets. It does
not flip `research/taskview_bom_scaling.SEMANTIC_FRONTIER_INFERENCE_AUTHORIZED`.

Live result: `results/c2_campaign_report.json`

```text
provider: gpt-5.6-sol-high
calls: 2
decisions: ACCEPT, ACCEPT
grounding: valid packet spans only
insert: ordinary BASE assert
frontier after insert: 0
derived relations: unchanged
```
