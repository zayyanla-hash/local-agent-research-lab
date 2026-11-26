# WeightRegressionBench 0.1.0 standalone package

Compare matched static tool-call observations with a frozen control using the included regression gate. It checks identity and alignment and reports new losses, gains, and configured metric guards. The AST checker validates records without invoking their named functions. Python 3.11 or newer suffices.

```sh
shasum -a 256 -c SHA256SUMS
python3 bench.py sample
python3 bench.py cases synthetic
python3 bench.py score synthetic fixtures/synthetic-pass.jsonl fixtures/synthetic.json baseline.json
python3 bench.py score synthetic fixtures/synthetic-fail.jsonl fixtures/synthetic.json candidate.json
python3 -m regression.gate freeze baseline.json fixtures/profile.json frozen.json
python3 -m regression.gate compare baseline.json candidate.json frozen.json --output report.json
```

The last command intentionally exits 1 to flag the broken control. Six fictional arithmetic and inventory examples exercise the static checker and gate. Their visible labels are unit smoke data.

Obtain BFCL questions and answers from the pinned upstream project under its applicable terms. The historical Simple Python inputs are `bfcl_eval/data/BFCL_v4_simple_python.json` with SHA-256 `82dd63ba502eb2520c6b5d1d9a5c4b590e03ff261565175561f6228a367d1991`. The matching reference file is `bfcl_eval/data/possible_answer/BFCL_v4_simple_python.json` with SHA-256 `90cd5bc653690ee8e459b5b3f3fc9458606f7f3fcbf795bb51b7dc581f8c86dc`. Pair rows by ID and combine each question row's `id`, `question`, and `function` with the matching answer row's `ground_truth` as JSONL, using `schema/case.schema.json`. Use the same file for both arms and caller-supplied observations plus metadata following the other schemas. [Pinned BFCL source and data](https://github.com/ShishirPatil/gorilla/tree/f7cf7359b7ac615a0b294831c5ba2bc95ee4a000/berkeley-function-call-leaderboard), [BFCL data publisher card](https://huggingface.co/datasets/gorilla-llm/Berkeley-Function-Calling-Leaderboard/blob/64d44ccd13f3351d17c33951af5ef1bd6e10153c/README.md).

```sh
python3 bench.py cases bfcl --cases YOUR-BFCL-CASES.jsonl
python3 bench.py score bfcl YOUR-OBSERVATIONS.jsonl YOUR-METADATA.json ARCHIVE.json --cases YOUR-BFCL-CASES.jsonl
```

The upstream BFCL AST checker, type mappings and converters under `bfcl_eval/` derive from Gorilla at the commit above. This package retains the upstream Apache 2.0 license at `licenses/Apache-2.0.txt`. The package isolates the static Python checker from the full provider harness using a modified local model-mapping shim. The other six files under `bfcl_eval/` match the pinned upstream bytes. The CLI's comparator is limited to normalized `simple_python` static calls and provides no official leaderboard result.

Licensing and attribution are in the package's `DISTRIBUTION.md`.
