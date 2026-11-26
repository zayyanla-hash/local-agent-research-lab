# MCP-EnforceBench 1.0.0 standalone package

Grade fictional grant-scope and evidence-grounding decisions on CPU. The scope track checks the exact decision and false permissions. The grounding track separately measures status, the evidence ID, their joint result, and inappropriate clearance or abstention. The package runs no connector and performs no actions on the proposal. Python 3.11 or newer suffices.

```sh
shasum -a 256 -c SHA256SUMS
python3 bench.py check --track scope
python3 bench.py check --track grounding
python3 bench.py reference --track grounding > toy-predictions.jsonl
python3 bench.py grade --track grounding --predictions toy-predictions.jsonl
```

The package contains two fictional scope and three fictional grounding controls with known answers. Both tracks use rule-based reference decisions as smoke controls. Submit your own model responses for the included IDs using `schemas/records.schema.json`. For a separate fixture set, pass matching `--inputs YOUR-INPUTS.jsonl` and `--answers YOUR-ANSWERS.jsonl` to `grade` or `check`. The data provides no estimate of production authorization accuracy or security.

Licensing and attribution are in the package's `DISTRIBUTION.md`.
