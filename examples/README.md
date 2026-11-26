# Two local reproductions

## Reconstruct edited parameter bytes

Use Python 3.11 or newer and the original model.safetensors from the pinned community conversion. The historical study used that checkpoint for its BF16 final normalization tensor. The distributed step-12 WeightForge deployment is a different artifact. [Historical checkpoint files](https://huggingface.co/mlx-community/Qwen3.5-4B-MLX-4bit/tree/32f3e8ecf65426fc3306969496342d504bfa13f3)

From the GitHub package root:

```sh
python3 examples/parameter-replay/replay.py "$HISTORICAL_CHECKPOINT/model.safetensors"
```

The CPU verifier checks the checkpoint hash and reconstructs two parameter vectors in memory. It compares their bytes against the targeted and matched-random hashes. The archived native experiment also restored the original logits and generation. This CPU command reproduces the tensor calculation; it performs no generation. [Parameter edits and measured restoration digests](parameter-replay/patch.json)

## Validate scanner explanations

These software tests exercise the lab's validator on benign, inert scanner-shaped reports. They check preserved source references, field-level evidence, abstention and rejection. They do not inspect a target or measure learned model quality.

```sh
cd examples/scanner
python3 -m pytest -q tests
```

The command requires pytest. The validator itself uses the Python standard library. It sits outside Sentry's advisory classifier and consumes existing findings.
