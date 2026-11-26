# AgentEfficiencyBench 0.1.0 standalone package

Replay multi-turn JSON tool traces in a fictional in-memory SQLite workspace. The runner scores committed state, attempted tool calls, errors, denials, redundant reads, and forbidden changes. It compares observed counts and timing across matched arms. Python 3.11 or newer suffices.

```sh
shasum -a 256 -c SHA256SUMS
python3 bench.py sample
python3 bench.py cases --variant skill
python3 bench.py reference
python3 bench.py skill fixtures/control.jsonl fixtures/candidate.jsonl
python3 bench.py score YOUR-TRACES.jsonl --cases YOUR-CASES.jsonl
```

The smoke controls cover two newly authored supply-shelf workflows. The correct paired trace resolves one deliberate error. Its token counts and wall time are fictional. Provide a case manifest and matched observations following the files under `schema/` to evaluate a newly collected run. The deterministic reference supports the named workflows implemented in `agentbench/strategies.py`.

The historical package also evaluated workflows from a lab validation split and demonstration utterances from MASSIVE TRAIN. Obtain the latter separately from the publisher under its attribution terms if reproducing the historical study. MASSIVE's inputs require the historical benchmark's study mapping. [Official MASSIVE repository](https://github.com/alexa/massive), [publisher notice](https://github.com/alexa/massive/blob/main/NOTICE.md), [pinned en-US training file](https://huggingface.co/datasets/AmazonScience/massive/blob/ed58ac423a2f4121720918bf5301577edce4ffd3/en-US/train/0000.parquet), [pinned dataset card](https://huggingface.co/datasets/AmazonScience/massive/blob/ff6bd8e4b27c3543e4f8fe2108f32bb95a6f8740/README.md).

Licensing and attribution are in the package's `DISTRIBUTION.md`.
