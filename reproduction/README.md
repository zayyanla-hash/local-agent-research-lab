# Reproduce WeightForge's four-category BFCL comparison

This adapter uses the local checkpoint and tokenizer files plus a pinned external Gorilla checkout. Python 3.11 or newer can verify fingerprints and case preparation. For inference or parent conversion, use Apple Silicon and the pinned [MLX runtime](requirements.txt). The original evaluation used an Apple M5 Pro with 48 GiB unified memory.

The package's expected outcome is the archived static Python comparison below. [Pins and archived category totals](pins.json) · [Offline CPU equivalence receipt](cpu-verification.json)

| BFCL v4 category | Matched INT4 Qwen parent | WeightForge step-12 INT4 |
|---|---:|---:|
| Simple Python | 343/400 | 362/400 |
| Multiple Python | 185/200 | 187/200 |
| Parallel Python | 84/200 | 124/200 |
| Parallel Multiple Python | 87/200 | 120/200 |
| Descriptive total | 699/1,000 | 793/1,000 |

## Prepare the pinned inputs

Use a Gorilla checkout of revision `f7cf7359b7ac615a0b294831c5ba2bc95ee4a000`. Set `WF_BFCL_SOURCE` to that checkout, `WF_STEP12_INT4` to the staged WeightForge fused INT4 package, and `WF_PARENT_INT4` to either the exact existing control or the destination for the conversion below. The verifier checks source and scorer bytes against [pins.json](pins.json).

The control is the **unadapted** BF16 `Qwen/Qwen3.5-4B` from revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, converted directly to affine INT4 group size 64 using MLX-LM 0.31.3. Its `model.safetensors` SHA-256 is `d58b87def677c7b3235e21cdca85289a162a5ba8949687b9573592e3c74cd477`. The fused step-12 package's weight SHA-256 is `69ac38a5e194765e3d489be1a1ac0e4a95a31201c83c1e256153a7180115ed73`. The chat template, tokenizer, configuration and index checksums also apply to both arms.

For local conversion, set `WF_UPSTREAM_BF16` to a directory containing the exact BF16 revision. With network access available for acquisition only, this command downloads the pinned upstream files listed in the manifest. The original Qwen material is under Apache 2.0. [Pinned source weights and license](https://huggingface.co/Qwen/Qwen3.5-4B/tree/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a)

```sh
export WF_UPSTREAM_BF16
python3 - <<'PY'
import json, os
from pathlib import Path
from huggingface_hub import snapshot_download

source = json.loads(Path("pins.json").read_text())["models"]["upstream"]
snapshot_download(repo_id=source["repository"], revision=source["revision"],
                  allow_patterns=list(source["verified_files"]),
                  local_dir=os.environ["WF_UPSTREAM_BF16"], token=False)
PY
```

Run the following from this reproduction directory after installing the pinned runtime. The parent output path must be new. The converter verifies every upstream file before conversion and all six control files afterward. If the post-conversion hash differs, use the byte-matched control artifact before making an exact-reproduction comparison.

```sh
profile='(version 1)(allow default)(deny network*)'
sandbox-exec -p "$profile" python3 -B bfcl.py derive-base "$WF_UPSTREAM_BF16" "$WF_PARENT_INT4"
python3 -B bfcl.py verify --bfcl "$WF_BFCL_SOURCE" \
  --parent "$WF_PARENT_INT4" --step12 "$WF_STEP12_INT4"
```

## Run the paired method

You can select one category at a time. This intentionally opt-in command runs all four and returns only aggregate outcomes.

```sh
profile='(version 1)(allow default)(deny network*)'
sandbox-exec -p "$profile" python3 -B bfcl.py run \
  --bfcl "$WF_BFCL_SOURCE" --parent "$WF_PARENT_INT4" --step12 "$WF_STEP12_INT4" \
  --suite simple_python --suite multiple --suite parallel --suite parallel_multiple
```

Official source order, the original prompt and function schemas, native Qwen template and parser, greedy decoding, no thinking, seed 17, batches of 16 and a 192-token cap reproduce the historical task setup. The last batch uses the remaining cases. Native call parsing retains the original malformed-envelope and parse-error rules. The comparator feeds decoded calls into the unmodified upstream Python AST checker. Results cover static function and argument accuracy across these categories. The adapter's output consists of paired aggregate counts.

The CPU verification regenerated prompt lengths and re-decoded archived token IDs, with exact agreement on parsed calls, parser errors, AST correctness and grader error types for all 2,000 recorded observations. It ran from a fresh directory with network and original checkout access denied. It made zero model inference calls. This is a verification of preparation, parsing and grading against the archived observations. The reproduction directory contains code, fingerprint references and aggregate counts.
