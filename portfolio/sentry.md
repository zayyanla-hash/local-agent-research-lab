# MCP Guard Sentry · Does the proposed action match the request?

A read-only operation can be valid under application policy and still serve a different purpose from the one a user authorized. I built an advisory classifier around that distinction. It reads the stated intent and a proposed action, then scores three fixed choices. The deterministic layer retains control of execution and factual scanner findings.

With a rank-4 adapter on Qwen3-1.7B and the same three-example prompt, correct native contextual decisions rose from **135 to 158 out of 232**. These were open development records in two purposes, alarm and media; some records share a source utterance. The adapter recognized 101/108 definite mismatches and none of the 16 unresolved cases. The result is a development signal about understanding purpose, with no independent deployment efficacy estimate.

The trade-off matters for a review queue. At a 0.90 top-score threshold, the parent made 185 decisions with 60 errors. The adapter made 16 with two errors. An independently defined calibration rule fitted on a separate audio-level calibration partition also reversed the headline ordering on the 232 cases: the parent scored 112 and the adapter 101. The thresholds answer different questions and neither supports a production false-positive claim.

An earlier 0.6B INT4 generative artifact returned zero fully contract-valid assessments on 36 held authorization envelopes. It remains quarantined. Independent accuracy for source-line scanner explanations remains unmeasured. These two limits shaped the design: the release adapter offers a narrow contextual signal, and the independent scanner and dispatcher supply findings and enforce permissions.

[Evidence and receipts](../evidence/) · [Model and data provenance](../provenance/README.md) · [Validator software example](../examples/README.md) · [Technical manuscripts](../manuscripts/)

© 2026 Zayyan Latif. All rights reserved.
