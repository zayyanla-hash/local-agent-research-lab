# Model, data, and run provenance

[The registry](registry.json) records model and tokenizer checksums, training dataset lineage, measured protocol boundaries, and the original lab records for both release targets. [Replay instructions](replay.md) distinguish standalone checks from reconstructions that need the original source lab checkout. [Aggregate replay evidence](../evidence/replay-aggregates.json) contains the result of regrading archived records. Weights, prompt and test records, and result traces with raw model text remain outside this GitHub evidence directory.

| Release target | Exact artifact | What it measures |
| --- | --- | --- |
| WeightForge-4B-Tools-v0.1 | Step-12 rank-8 MLP LoRA fused in BF16 and converted to MLX affine INT4, group 64. Weight file SHA-256 `69ac38a5e194765e3d489be1a1ac0e4a95a31201c83c1e256153a7180115ed73` | Structured tool-call generation and local simulated workflows. Unchanged same-source INT4 comparator SHA-256 `d58b87def677c7b3235e21cdca85289a162a5ba8949687b9573592e3c74cd477` |
| Sentry 1.7B Trusted-Intent Advisory | Step-48 rank-4 MLX LoRA on the original Qwen3-1.7B BF16 weights. Adapter SHA-256 `426dcc67cffdafaf5c4031cf939c529afbdf71adc1cacd561d000feeb1e56f13` | An advisory status for a trusted request and an individually permitted fictional proposal. The host resolves the supplied evidence and owns execution |

The WeightForge checkpoint derives from Qwen3.5-4B revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`. The full upstream BF16 snapshot includes vision tensors, and the release evaluation covers the text tool interface. Sentry requires the exact publisher BF16 Qwen3-1.7B snapshot at `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`; the original weight shards together contain 4,063,515,592 bytes, and the attached adapter contains 4,992,631 bytes. The package-specific model manifests record the unchanged weight identities separately from the sanitized inference configuration. Upstream model terms are Apache-2.0. [WeightForge parent](https://huggingface.co/Qwen/Qwen3.5-4B/tree/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a) · [Sentry parent](https://huggingface.co/Qwen/Qwen3-1.7B/tree/70d244cc86ccca08cf5af4e1e306ecf908b1ad5e) · [Distribution status](../PUBLICATION-TERMS.md)

## License scope and destinations

Rights holder Zayyan Latif approved Apache-2.0 for the original model adaptations and source code, and CC BY 4.0 for the original research papers, figures, and eligible synthetic datasets. Third-party rights and attribution remain under their respective terms. The owner approved publication of the staged inventory at the destinations below. The registry identifies the exact local package bytes prepared for transfer. [Publication terms](../PUBLICATION-TERMS.md) · [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

| Staged material | Approved destination |
| --- | --- |
| Research code, evidence, and benchmark packages | `zayyanla-hash/local-agent-research-lab` (GitHub) |
| WeightForge step-12 affine INT4 export | `zayyanxlatif/WeightForge-4B-Tools-INT4` (Hugging Face) |
| Sentry Qwen3-1.7B rank-4 BF16 advisory adapter | `zayyanxlatif/Sentry-1.7B-Intent-Advisory-LoRA` (Hugging Face) |

## Training and data

WeightForge's trainer sampled 12 updates from a pool of 72 original simulated training episodes across 18 families, with 204 eligible supervised turns. The selected update trace covers nine distinct episodes in seven families, 7,850 total sequence positions, and 428 assistant loss positions. Only the last two text blocks' gate, up, and down projections were adapted, with 565,248 trainable scalars. The archived selected run recorded 6.01 seconds of update intervals, 13.37 seconds through final checkpoint and validation, and a 9.547 GB MLX allocator peak. The 14 public development episodes span seven families. The BFCL study and independent simulation aggregate are evaluation evidence.

Sentry's source is the pinned English TRAIN partition of MASSIVE v1.1, attributed to Amazon.com, Inc. or its affiliates and the MASSIVE authors. The underlying English text comes from SLURP by Emanuele Bastianelli, Andrea Vanzo, Paweł Świętojański, and Verena Rieser. Both text sources use CC BY 4.0. The adaptation pairs utterances with harmless mock proposals, receipts, and reference IDs. The trainer used a 184-row pilot from a 464-row fitting pool, plus a 12-row diagnostic sampled from the pilot itself. Separate purpose families supply 64 calibration decisions and 232 development decisions. Adam ran 48 updates with batch size four, on eight blocks with 1,245,184 trainable scalars. The archival log counted 384 supervised label/EOS positions over approximately 12.32 seconds of update intervals, with a 6.327 GB training allocator peak. The trainer weighted the label position three times the EOS position. [MASSIVE dataset card](https://huggingface.co/datasets/AmazonScience/massive/blob/ff6bd8e4b27c3543e4f8fe2108f32bb95a6f8740/README.md) · [Pinned source file](https://huggingface.co/datasets/AmazonScience/massive/blob/ed58ac423a2f4121720918bf5301577edce4ffd3/en-US/train/0000.parquet) · [SLURP source and license](https://github.com/pswietojanski/slurp/blob/8eb16545762be97ace75334109d73824217311f1/README.md#license)

## Runtime observations by artifact

| Measured workload | Matched parent | Adapted release target |
| --- | ---: | ---: |
| WeightForge MLX-LM official serial generation, 512 prompt and 64 output tokens | 97.8 generated tok/s | 98.8 generated tok/s |
| WeightForge official serial generation, 2,048 prompt and 64 output tokens | 97.4 generated tok/s | 97.3 generated tok/s |
| WeightForge official batch-four aggregate generation, 2,048 prompt tokens, 64 output per request | 239.7 generated tok/s | 240.3 generated tok/s |
| WeightForge official wall-clock output rate, 2,048 prompt tokens, one → four requests | 40.0 → 52.8 tok/s | 39.2 → 53.2 tok/s |
| WeightForge native public simulation, median complete episode across 14 episodes | 2.117 s | 2.148 s |
| Sentry three-logit forward, 232 matched examples, 238–270 prompt tokens | 36.64 ms median, 37.62 ms P95 | 42.34 ms median, 44.00 ms P95 |
| Sentry MLX allocator high-water mark in those processes | 3.683 GB | 4.002 GB |

WeightForge official timings use MLX 0.32.2 and MLX-LM 0.31.3 on an Apple M5 Pro with 48 GiB unified memory. They use seeded synthetic token IDs, one warmup per cell, and three timed trials. The batch column counts the entire batch. Wall-clock output rate includes prompt processing. In the separate synthetic-copy stream, median process spawn to first engine token for WeightForge deployment was 1.612 s at 512 prompt tokens and 2.225 s at 2,048. Resident worker TTFT at those lengths was 325 ms and 977 ms. File-cache state was uncontrolled. The 2,048-token resident block completed 22 copies in 31.0 s, with 3.86 GiB peak MLX allocation and 2.80 GiB peak process RSS. Those two statistics and the host's unified memory capacity describe different quantities. Energy per request was unmeasured. [Installed benchmark source](https://github.com/ml-explore/mlx-lm/blob/v0.31.3/mlx_lm/benchmark.py)

Sentry timings cover selecting the matching-scope trusted request for the input, rendering and tokenizing the fixed prompt, and reading three final-position logits after a single forward pass. Each capture process warmed the cohort before measuring. The timings exclude model load, streamed decoding, post-model attachment of evidence references, response formatting, and dispatch. The allocator high-water mark can include earlier calibration or warmup in that process. These are archived research-run figures for the exact adapter weights, separate from smoke timing for the portable wrapper. The historical 0.6B INT4 generation benchmarks belong to a different model. WeightForge QV64, historical Sentry 0.6B, and experimental INT8 controls remain research comparators outside the two release targets.

## Outcome boundaries

WeightForge improved from 699 to 793 out of 1,000 cases over four static Python BFCL V4 categories, with 101 gains and seven losses. The official AST checker scored function calls and arguments. The independent 16-episode simulator gave the unadapted parent 15/16 and WeightForge 14/16. Sentry reached 158/232 native status-and-evidence decisions against the same-prompt parent's 135/232, with 43 gains and 20 losses. It matched nine of 124 mismatched or unresolved requests, compared with 38 for the parent, and clarified none of 16 unresolved requests. Under calibration, its joint result was 101/232 versus 112/232 for the parent. These results support scoped research comparisons. The two model packages remain experimental. [Aggregate replay evidence](../evidence/replay-aggregates.json) · [Run registry](registry.json)
