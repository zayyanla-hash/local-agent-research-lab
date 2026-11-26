# Standalone benchmark packages

The four standalone packages contain runners, schemas, and small fictional smoke controls. Zayyan Latif approved Apache-2.0 for original software and CC BY 4.0 for the original fictional fixture data listed in each package's `DISTRIBUTION.md`. Zayyan Latif approved these four archives for publication. [Publication terms](../PUBLICATION-TERMS.md) · [Apache License 2.0](licenses/Apache-2.0.txt) · [CC BY 4.0](licenses/CC-BY-4.0.txt).

The smoke outcomes below verify the tooling on fabricated examples.

| Proposed archive | Offline smoke result | Standalone instructions |
| --- | --- | --- |
| [AgentEfficiencyBench 0.1.0](AgentEfficiencyBench-0.1.0-local-rc1.zip) | Deterministic reference 2/2. Paired control 1/2 and corrected trace 2/2. | [Replay and compare workflow traces](package-readmes/AgentEfficiencyBench-0.1.0.md) |
| [WeightRegressionBench 0.1.0](WeightRegressionBench-0.1.0-local-rc1.zip) | Six fictional static calls. Identical control passes and the deliberately broken arm fails. Caller-provided case import verified. | [Grade static calls and acquire BFCL inputs](package-readmes/WeightRegressionBench-0.1.0.md) |
| [MCP-EnforceBench 1.0.0](MCP-EnforceBench-1.0.0-local-rc1.zip) | Scope 2/2 and joint evidence decisions 3/3. Caller-provided cases and answers accepted. | [Grade mock policy and evidence decisions](package-readmes/MCP-EnforceBench-1.0.0.md) |
| [LocalInferenceBench 1.0.0](LocalInferenceBench-1.0.0-local-rc1.zip) | Exact-copy output 3/3 on fabricated observations. Cold and resident report groups render. | [Replay, grade, or capture local measurements](package-readmes/LocalInferenceBench-1.0.0.md) |

Verify the archive bytes before extracting.

```sh
shasum -a 256 -c SHA256SUMS
python3 -B verify.py --staged-only
```

The second command runs the full smoke suite on macOS without network access. It also denies access to the local home directory and confines writes to a temporary directory. From an individual extracted package, the README lists portable Python 3.11+ smoke commands. Local MLX capture is optional and was outside this package verification.

## Archive review

The [machine-readable audit](AUDIT.json) records both sets of exact hashes, member changes, permissions and smoke outcomes. The verifier inspects every ZIP member, tests its CRC and SHA-256, checks the full relative path and file type, parses JSON formats, and looks for personal filesystem paths and common credential markers. It checks the scoped notices, license texts, and exact permitted JSONL inventory. Every file in the proposed archives is regular mode 0644. The package scope excludes checkpoint weights, historical validation cases and model observations, external benchmark fixtures and their answers, and old paired traces. The small visible answers in these archives belong to the fictional smoke controls listed above.

The WeightRegressionBench candidate preserves its pinned Apache-2.0 BFCL checker, mappings and converters. It marks the one model-config shim modified for offline use and ships the upstream license text. Its package instructions point to the exact upstream BFCL case and reference inputs for a locally supplied run. The AgentEfficiencyBench candidate provides publisher acquisition and attribution for the historical MASSIVE training source. [Pinned Gorilla license](https://github.com/ShishirPatil/gorilla/blob/f7cf7359b7ac615a0b294831c5ba2bc95ee4a000/LICENSE) · [MASSIVE publisher notice](https://github.com/alexa/massive/blob/main/NOTICE.md).

The four original ZIPs remain byte-identical in the private lab's historical `benchmark-releases/` directory. The historical archives and associated data are outside the approved GitHub publication inventory, which uses a clean export. The research repository's existing Git history contains historical package inputs.

Private lab maintainers can reproduce the approved ZIPs from the historical archives with `python3 -B build.py` and repeat both sides of the audit with `python3 -B verify.py`. Both commands run from this directory. The standalone ZIPs and staged-only check run independently of the private lab checkout.
