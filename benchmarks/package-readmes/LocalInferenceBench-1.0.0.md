# LocalInferenceBench 1.0.0 standalone package

Validate exact-copy model observations and summarize cold and resident request measurements separately. The validator checks exact task output, context length, cache reuse, token counts, prompt identity, timings and memory. Python 3.11 or newer suffices for grading.

```sh
shasum -a 256 -c SHA256SUMS
python3 bench.py replay
python3 bench.py grade --observations YOUR-OBSERVATIONS.jsonl
```

The three bundled rows use an original exact-copy string and fabricated observations. They cover a cold 512-token request and resident 512- and 2,048-token requests. Their times, memory sizes and token hashes are placeholders for validating the report format.

Capture new measurements with a trusted existing local MLX model and `mlx-lm` on Apple Silicon. Use a fresh output location and the same workload settings for paired arms. The capture script requires a network-denying policy and checks it before loading the local checkpoint.

```sh
sandbox-exec -p '(version 1)(allow default)(deny network*)' python3 capture.py \
  /path/to/local/model --variant YOUR-ARM --output YOUR-OBSERVATIONS.jsonl --smoke
python3 bench.py grade --observations YOUR-OBSERVATIONS.jsonl
```

Omit `--smoke` for the full capture schedule. A fresh capture includes model file hashes and runtime versions in its receipt. Record host and concurrency conditions separately for comparisons. Licensing and attribution are in the package's `DISTRIBUTION.md`.
