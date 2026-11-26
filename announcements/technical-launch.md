# Technical announcement drafts

## Research launch

I built two experimental local models to study where an agent's decisions go wrong.

WeightForge's step-12 INT4 checkpoint passed 793/1,000 cases on four BFCL V4 static Python categories, up from 699 for its matched INT4 parent. Parallel calls accounted for much of the gain. On 16 independently scored workflows, however, the same artifact finished one fewer task. In a separate retail simulation its dispatcher blocked an attempted change before the user gave consent.

MCP Guard Sentry's 1.7B advisory adapter raised correct contextual decisions from 135 to 158 on 232 development records. At a high score threshold it also answered far fewer cases. The scanner supplies factual findings and the dispatcher enforces permissions. The earlier 0.6B checkpoint remains quarantined after returning zero contract-valid assessments on 36 independent authorization cases.

The accompanying research traces a 16-parameter edit that changed a logit margin and left the wrong output intact, measures local inference on Apple Silicon, and includes four benchmark packages with reproducible controls. Start with the technical write-ups for the exact models, evaluation scopes and negative findings. [Technical manuscripts](../manuscripts/README.md) · [Benchmark packages](../benchmarks/README.md)

## X caption

WeightForge INT4 passed 699 → 793/1,000 BFCL V4 static Python cases and 15 → 14/16 held workflows. Sentry 1.7B scored 135 → 158/232 on intent development with less high-confidence coverage. Both are experimental.

## Founder-facing note

WeightForge improved the share of correctly answered cases on four standardized tool-use categories. A separate workflow test caught a recovery regression that the static benchmark missed. Sentry improved intent matching on a small internal development cohort, but its high-confidence answer rate fell sharply. These are working research examples of how to evaluate a local agent before trusting it with state changes.

© 2026 Zayyan Latif. All rights reserved.
