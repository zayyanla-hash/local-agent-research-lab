# Quantitative highlights

| What I built | Verified result | Evidence boundary |
|---|---|---|
| An INT4 function-calling adaptation | +94 correctly answered cases, 699 → 793 out of 1,000, with 101 gains and seven losses | Four static Python BFCL V4 categories. Held workflow completion fell 15 → 14 of 16. |
| A local contextual advisory adapter | +23 correct decisions, 135 → 158 of 232 | Same-prompt development comparison over two purposes. At ≥0.90, decision coverage fell from 185 to 16 cases. |
| A reversible weight-edit experiment | 16 parameters edited; +0.250-logit target margin; exact rollback | One fitted prefix. The duplicate-ID output persisted. |
| A local inference measurement suite | 72 fixed-length timed trials and 341 streaming requests across the hardware study | Selected WeightForge INT4 decoded 97.3 tokens/s at 2,048 input tokens and batch one. Other measured artifacts had separate endpoints. |
| Four independently runnable benchmark packages | AgentEfficiencyBench, MCP-EnforceBench, LocalInferenceBench and WeightRegressionBench | Archive checks and software tests measure reproducibility. Model quality comes from task outcomes. |

[WeightForge](weightforge.md) · [Sentry](sentry.md) · [Reference measurements](../provenance/README.md)

© 2026 Zayyan Latif. All rights reserved.
