# Measured figures

Original figure artwork is © 2026 Zayyan Latif and licensed under Creative Commons Attribution 4.0 International. Credit Zayyan Latif when reusing the figures. [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

Each PNG has an SVG companion. The [measurement inventory](measurements.json) records plotted values, figure hashes and source-archive fingerprints. All plots are original lab renders from archived measurements. They contain aggregate observations and omit source text and examples. [File checksums](SHA256SUMS) · [Benchmark scope](../benchmarks/README.md) · [Publication terms](../PUBLICATION-TERMS.md)

| Figure | Measurement and scope |
|---|---|
| [Public tool and code results](public-weightforge.png) · [SVG](public-weightforge.svg) | The matched step-12 G64 INT4 pair on four complete BFCL v4 static Python categories and 164 HumanEval+ tasks. The confidence intervals are paired item-bootstrap intervals. The augmented code scores include a reference-validated memory-limit replay of one case per arm. |
| [Accuracy and latency frontier](agent-accuracy-latency-pareto.png) · [SVG](agent-accuracy-latency-pareto.svg) | Seven policies share the same 12 public development workflows. Cost counts all attempted episodes. Equivalent policy plans reuse recorded outcomes. |
| [Same-source quantization](same-source-quantization.png) · [SVG](same-source-quantization.svg) | Qwen3.5-0.8B BF16, INT4 group 64 and INT4 group 32 use the same 12 development and 12 public-validation prompts. Peak memory and median generation time use the validation observations. |
| [Resident memory and throughput](resident-memory-throughput.png) · [SVG](resident-memory-throughput.svg) | One warm exact-copy request per model and context. The two models share identical input token IDs across three context lengths. |
| [Reciprocal weight localization](reciprocal-weight-localization.png) · [SVG](reciprocal-weight-localization.svg) | Twenty-four one-block interventions per recipient on one selected warehouse prompt. Opening logits and recovered native behavior concern this case. |
| [Workflow ablations](workflow-ablations.png) · [SVG](workflow-ablations.svg) | Six variations of one incident lookup and 18 separate compact-call development workflows. Each panel has its own strict-success denominator. |
| [Query/value orientation ablation](qv-orientation-ablation.png) · [SVG](qv-orientation-ablation.svg) | The intact update and eight seeded orientation controls on the same ten intentionally selected rescue prefixes. |
| [Advisory precision–recall](sentry-advisory-precision-recall.png) · [SVG](sentry-advisory-precision-recall.svg) | An earlier classifier on 40 synthetic matched authorization examples. Class prevalence is 50%. Equal scores enter jointly. The zero-recall endpoint uses the conventional precision of one. |
| [Grounding and evidence coverage](grounding-and-coverage.png) · [SVG](grounding-and-coverage.svg) | Doc2Dial evidence span choice on 34 TRAIN questions. The separate claim-support panel covers 42 supported, 42 opposing and 12 unresolved examples. |
| [Advisory confidence coverage](sentry-confidence-coverage.png) · [SVG](sentry-confidence-coverage.svg) | The Qwen3-1.7B rank-4 study on 232 open purpose decisions. Conditional error is undefined at zero coverage. Threshold points use archived three-way scores. |
| [Official inference memory and speed](official-precision-memory-throughput.png) · [SVG](official-precision-memory-throughput.svg) | Selected WeightForge step-12 and historical Sentry 0.6B checkpoints. Three trials per precision at 2,048 input tokens, 64 generated tokens and batch one. |
| [Benign alerts under harm-classifier policies](public-benign-guard-alerts.png) · [SVG](public-benign-guard-alerts.svg) | Matched benign XSTest and OR-Bench prompts use each guard's declared harm labels. PIGuard's NotInject count uses a separate corpus and label policy. |
| [Historical Sentry benign alerts](public-sentry.png) · [SVG](public-sentry.svg) | Exact historical 0.6B INT4 parent and derivative on all 339 benign NotInject prompts at their frozen cutoffs. There are no positive cases. |
| [Historical Sentry operating points](sentry-operating-points.png) · [SVG](sentry-operating-points.svg) | Post-hoc replay uses 12 suspicious and 18 benign independent synthetic examples. Six uncertain examples are excluded from discrimination metrics. Both 0.6B INT4 arms returned zero strict valid outputs across all 36. |

The [manuscripts](../manuscripts/README.md) credit the upstream models and evaluation projects. [Release index](../README.md)
