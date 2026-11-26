# Replay instructions

The [registry](registry.json) pins source revisions, selected artifacts, and SHA-256 digests. Commands under the source lab sections require that checkout and the named local materials. Commands for the separately packaged smoke tests require only the package, its stated interpreter, and the exact artifacts. A smoke validates loading and the output contract on benign synthetic inputs. The measured evaluation uses different fixture cohorts.

## Verify the model packages

Run the package's checksum command from the respective model directory. The final research targets are the fused WeightForge step-12 MLX INT4 model and the matched Sentry Qwen3-1.7B BF16 rank-4 adapter. These commands use local staged packages. Put the exact WeightForge files in its package folder and the exact upstream BF16 Sentry base in a separate local folder before running inference.

```sh
# From the WeightForge package
shasum -a 256 -c UPLOAD-SHA256SUMS
shasum -a 256 -c MODEL-SHA256SUMS
WF_SMOKE_PYTHON="${WF_SMOKE_PYTHON:-python3}"
sandbox-exec -p '(version 1)(allow default)(deny network*)(deny file-write*)' \
  env HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 \
  "$WF_SMOKE_PYTHON" -I -B smoke.py

# From the Sentry package, with SENTRY_BASE set to the exact pinned BF16 snapshot
shasum -a 256 -c SHA256SUMS
sandbox-exec -p '(version 1)(allow default)(deny network*)' \
  env HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 \
  "$MLX_PYTHON" assess.py --base "$SENTRY_BASE" --input smoke-input.jsonl
```

Use the Sentry package's `--base-only` mode for the unadapted comparator. Acquire its base from the [exact publisher revision](https://huggingface.co/Qwen/Qwen3-1.7B/tree/70d244cc86ccca08cf5af4e1e306ecf908b1ad5e). Assessments in the portable package stay advisory.

## Benchmark archive samples

Unpack the corresponding [benchmark archive](../benchmarks/), verify its supplied checksum manifest, then run the command from its top-level directory. Built-in examples and documented sample replay are local CPU checks. The authorized release archives contain lab-authored fixtures. Historical research archives use different hashes and datasets.

| Benchmark family | CPU commands from its package |
| --- | --- |
| AgentEfficiencyBench | `python3 bench.py sample` |
| WeightRegressionBench | `python3 bench.py sample` |
| MCP-EnforceBench | `python3 bench.py check --track scope` and `python3 bench.py check --track grounding` |
| LocalInferenceBench | `python3 bench.py replay` |

## Archived grading in the source lab

The internal replay reads the original BFCL static reports and Sentry three-label captures already retained by the source lab. It recomputes call and argument grades and native label accuracy from those records. It also feeds the stored Sentry logits through the staged resolver and renderer and checks the resulting status and evidence jointly. Executing this command requires the MLX Python environment to load the verified local tokenizers. The replay uses public or development-visible cohorts and verifies the staged model artifact fingerprints. The public file contains only aggregate scores and their source commitments.

```sh
sandbox-exec -p '(version 1)(allow default)(deny network*)' \
  env HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 \
  "$HOME/.venvs/mlx/bin/python" final-release/review/replay_archived.py \
  runs/final-portable-replay-new.json
```

The historical MBPP+ prefix is separately reproducible, with its own [official release](https://github.com/evalplus/mbppplus_release/releases/tag/v0.2.0), data SHA, and pinned EvalPlus checkout. The raw candidate programs remain in the source lab. In that checkout, the frozen recipe is recorded at `docs/benchmark-expansion/mbpp-results.md` and the evaluator entry point is `python -m evals.mbpp_expansion --help`. That experiment compares the QV64 research adapter to its INT4 parent.

## WeightForge source lab reconstruction

Use fresh output paths, the frozen source revision and lab dependency lock, and the same offline MLX runtime. The public upstream fetch is separate from training. The data generator produces original local simulations. The direct training command below reproduces the selected 12-update adapter into its own tag. The public-development scoring command uses the existing frozen INT4 exports. The source lab release protocol documents BF16 fusion and INT4 conversion separately in `releases/artifacts/WeightForge-4B-Tools-v0.1/protocol.md`.

```sh
"$HOME/.venvs/mlx/bin/python" -m releases.weightforge_fetch
uv run --locked python -m releases.weightforge_data
sandbox-exec -p '(version 1)(allow default)(deny network*)' \
  env HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 \
  "$HOME/.venvs/mlx/bin/python" -m releases.weightforge_train \
  --steps 12 --output-tag release-provenance-reproduction

weightforge=models/releases/WeightForge-4B-Tools-v0.1
shasum -a 256 "$weightforge/release-provenance-reproduction/adapters.safetensors"
.venv/bin/python -m releases.weightforge_eval \
  --cases "$weightforge/data/valid.cases.jsonl" \
  --output runs/weightforge-final-public-dev-replay-new \
  --arm "base-int4=$weightforge/base-int4" \
  --arm "deploy-int4=$weightforge/deploy-int4"
```

The selected adapter digest is `5aad4b81ff36f5f1278adf342501a2ce6e6b656846737735e48b52efc7e7378d`. The direct trainer should run alone under the source lab's shared GPU lease, as described in that protocol.

## Apple inference engineering in the source lab

Use the verified models and local Apple MLX environment. The `--precision` option also creates a local INT8 experimental control from each adapted BF16 source. The historical Sentry 0.6B variants in the resulting scorecard belong to the older release experiment. Use the WeightForge `wf_deploy_int4` and `wf_parent_int4` rows for the final step-12 inference study.

```sh
.venv/bin/python -m performance.expansion_official runs/final-inference-official-new --precision
.venv/bin/python -m performance.expansion_serving runs/final-inference-serving-new
.venv/bin/python -m performance.expansion_scorecard \
  runs/final-inference-official-new runs/final-inference-serving-new \
  runs/final-inference-scorecard-new
```

These commands record fixed-output synthetic generation and independent streaming timings. The standalone benchmark samples use their own documented inputs and replay existing measurements.

## Sentry source lab reconstruction

Stage the [public MASSIVE source file](https://huggingface.co/datasets/AmazonScience/massive/blob/ed58ac423a2f4121720918bf5301577edce4ffd3/en-US/train/0000.parquet), the prior curated grouped and v3 state, and the pinned Qwen3-1.7B snapshot in the source lab paths named in `sentry/intent_lora_data.py`. The [registry](registry.json) identifies the original files and expected hashes. The earlier source and grouped-replay recipes are in `docs/redevelopment/sentry-trusted-intent.md` and `docs/redevelopment/sentry-trusted-intent-grouped.md`. Place the publisher snapshot manifest at `models/redevelopment/qwen3-1.7b/provenance.json` from the verified `docs/redevelopment/qwen3-1.7b-provenance.json`. The loader checks every source file before training or capture.

```sh
policy='(version 1)(allow default)(deny network*)'
engine="$HOME/.venvs/mlx/bin/python"
run=runs/sentry-rank4-provenance-reproduction-new
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
sandbox-exec -p "$policy" "$engine" -m sentry.intent_lora prepare "$run"
sandbox-exec -p "$policy" "$engine" -m sentry.intent_lora mask "$run"
sandbox-exec -p "$policy" "$engine" -m sentry.intent_lora train "$run" --tag rank4
sandbox-exec -p "$policy" "$engine" -m sentry.intent_lora capture "$run" --tag parent-fewshot
sandbox-exec -p "$policy" "$engine" -m sentry.intent_lora capture "$run" --tag rank4-fewshot
sandbox-exec -p "$policy" "$engine" -m sentry.intent_lora summarize "$run" --tag parent-fewshot
sandbox-exec -p "$policy" "$engine" -m sentry.intent_lora summarize "$run" --tag rank4-fewshot
```

Preparation requires the same pinned parquet reader used by the earlier curation code. An existing frozen `rank4` adapter can be staged into the new run instead of fitting before capture. The original model evaluation results record the same-prompt token audit and independent source attribution. The `native` part of each summary is the shipped decision mode. The calibration and factored follow-ups are research controls.
