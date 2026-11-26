# WeightForge and MCP Guard Sentry

Two experimental adaptations tackle different parts of local agent execution. WeightForge emits structured function calls. Sentry estimates whether a proposed action matches the user's stated purpose. The application owns the decision to execute.

| Selected artifact | Matched result | Where the result stops |
|---|---|---|
| WeightForge-4B-Tools, step-12 merged affine INT4 | 699 → **793 correct out of 1,000** on four BFCL V4 static Python categories. The model gained 101 cases and lost seven. | The independent multistep workflow result went from 15/16 to 14/16. A dispatcher blocked a premature write in a separate simulated retail pilot. |
| MCP Guard Sentry, Qwen3-1.7B BF16 plus rank-4 advisory adapter | 135 → **158 correct out of 232** contextual development decisions under the same three-example prompt. | At a score threshold of 0.90, the adapter decided 16 cases and missed two; the parent decided 185 and missed 60. The historical 0.6B INT4 checkpoint failed grounding on all 36 independent authorization envelopes and remains quarantined. |

Both models are **experimental research releases**. Use an independent dispatcher for real actions. Model files and runtime instructions are available in the two model repositories. [WeightForge on Hugging Face](https://huggingface.co/zayyanxlatif/WeightForge-4B-Tools-INT4) · [Sentry on Hugging Face](https://huggingface.co/zayyanxlatif/Sentry-1.7B-Intent-Advisory-LoRA). [Licenses and attribution](PUBLICATION-TERMS.md)

## Explore and reproduce

- [Manuscripts](manuscripts/) and [measured figures](figures/) cover tool calling and parameter interventions, contextual security, and local inference engineering.
- [Model and experiment provenance](provenance/README.md) identifies the exact artifacts, data and runtime; the [evidence directory](evidence/) supports the numerical claims.
- [Benchmark packages](benchmarks/) cover agent efficiency, policy enforcement, local inference and weight regression.
- [WeightForge BFCL reproduction](reproduction/README.md) verifies the exact four-category tool-call method using a pinned official checkout and local weights.
- [Runnable software examples](examples/README.md) reproduce a real weight-space comparison and exercise the deterministic scanner-evidence validator on inert records.
- [WeightForge case study](portfolio/weightforge.md), [Sentry case study](portfolio/sentry.md) and [quantitative highlights](portfolio/highlights.md) explain the engineering decisions and observed limitations.

The deployment platform for the measured model runs was an Apple M5 Pro with 48 GiB unified memory. Generated-token throughput, request latency, three-way classifier latency and complete workflow time have different measurement boundaries.
