# Reproducing the two score claims

Run from this directory with Python 3.9 or later.

```sh
python3 -I -S check_claims.py
```

The checker recomputes parent and candidate totals, paired gains and losses, and percentage-point differences from aggregate contingency tables. The JSON includes trace, dataset and model-file fingerprints for provenance. It contains no case identifiers, prompts, expected outputs, per-item labels or predictions. Reconstructing individual grades requires separately authorized source data and archived responses.

| Artifact and endpoint | Unchanged parent | Candidate | Paired change |
|---|---:|---:|---|
| WeightForge step-12 merged/requantized INT4, four BFCL v4 static Python categories | 699/1,000 | 793/1,000 | 101 gains, 7 losses, +9.4 percentage points |
| Sentry rank-4 adapter on Qwen3-1.7B BF16, status choice on open intent development data | 135/232 | 158/232 | 43 gains, 20 losses, +9.91 percentage points |

**WeightForge.** The internal offline replay parsed all 2,000 archived strings again with each checkpoint's native MLX-LM parser. It graded the parsed calls against the original pinned BFCL AST checker and compared each grade to the corresponding archived decision. All agreed. Four static Python categories measure structured calls without executing them. The score does not measure the full BFCL suite or multi-turn recovery. On the previously reported independent workflow gate the candidate completed 14/16 versus the matched parent's 15/16.

**Sentry.** The internal replay aligned each arm's 232 captured three-way logit vectors with the original open development IDs, then compared the highest-scoring status with the development annotation. The packaged resolver produced identical model-visible messages on every input. Passing each archived score vector through the packaged assessor yielded the same 135 and 158 exact status-plus-reference outputs, using its deterministic evidence renderer. Both arms used the same three-example prompt. These are two editorial purpose groups and repeated source utterances. The score does not measure generated evidence citations, calibrated authorization, scanner findings or independent security efficacy. The 38/232 pretrained NLI entry in the receipt uses its mapped raw entailment-class argmax on this endpoint. It does not stand in for a separately calibrated NLI policy.

Both replays verified the fingerprinted source weights. Neither generated fresh model responses. Hashes identify bytes; they do not independently authenticate who collected the traces. [Archival replay and aggregate fingerprints](replay-aggregates.json)
