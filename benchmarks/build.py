"""Derive standalone local-review candidates from the immutable historical ZIPs."""
from hashlib import sha256
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

HERE = Path(__file__).resolve().parent
HISTORY = HERE.parents[2] / "benchmark-releases"

AGENT = "AgentEfficiencyBench-0.1.0"
WEIGHT = "WeightRegressionBench-0.1.0"
MCP = "MCP-EnforceBench-1.0.0"
LOCAL = "LocalInferenceBench-1.0.0"
PROJECTS = (AGENT, WEIGHT, MCP, LOCAL)
FIXTURE_DATA = {
    AGENT: ("fixtures/smoke.jsonl", "fixtures/control.jsonl", "fixtures/candidate.jsonl"),
    WEIGHT: ("fixtures/synthetic.jsonl", "fixtures/synthetic-pass.jsonl", "fixtures/synthetic-fail.jsonl"),
    MCP: ("data/scope-inputs.jsonl", "data/scope-answers.jsonl", "data/grounding-inputs.jsonl",
          "data/grounding-answers.jsonl"),
    LOCAL: ("data/observations.jsonl",),
}

LAB_APACHE = "LICENSE"
LAB_CC_BY = "licenses/CC-BY-4.0.txt"
GORILLA_APACHE = "licenses/Apache-2.0.txt"


def distribution(project):
    lines = [
        "# Licensing and attribution",
        "",
        "Original software, schemas, and runner configuration are copyright 2026 Zayyan Latif.",
        "They are licensed under the [Apache License 2.0](LICENSE).",
        "",
        "The original fictional smoke data below are copyright 2026 Zayyan Latif and licensed under",
        "[Creative Commons Attribution 4.0 International](licenses/CC-BY-4.0.txt). Attribute the data",
        f"as \"{project} synthetic smoke fixtures by Zayyan Latif, CC BY 4.0\" and indicate changes.",
        "",
        *[f"- `{path}`" for path in FIXTURE_DATA[project]],
        "",
    ]
    if project == WEIGHT:
        lines += [
            "The BFCL modules under `bfcl_eval/` retain the upstream Gorilla",
            "[Apache License 2.0 and its notices](licenses/Apache-2.0.txt).",
            "The local `model_config.py` shim is marked as modified for offline use.",
            "[Pinned Gorilla source](https://github.com/ShishirPatil/gorilla/tree/f7cf7359b7ac615a0b294831c5ba2bc95ee4a000/berkeley-function-call-leaderboard).",
            "",
        ]
    lines += [
        "Obtained separately, upstream data retain publisher terms and attribution requirements.",
        "The bundled smoke data have visible expected behavior. Hardware scores, matched model results,",
        "and security assurance require separate evidence.",
        "",
    ]
    return "\n".join(lines)


def digest(body):
    return sha256(body).hexdigest()


def manifest(files):
    return "".join(f"{digest(body)}  {name}\n" for name, body in sorted(files.items())).encode()


def historical(name):
    filename = name + ".zip"
    expected = dict(line.split()[::-1] for line in (HISTORY / "SHA256SUMS").read_text().splitlines())
    archive = HISTORY / filename
    if digest(archive.read_bytes()) != expected[filename]:
        raise ValueError(f"Historical archive hash mismatch: {filename}")
    with ZipFile(archive) as source:
        files = {}
        for member in source.infolist():
            stem, separator, path = member.filename.partition("/")
            if stem != name or not separator or not path or path in files:
                raise ValueError(f"Unexpected historical member: {member.filename}")
            files[path] = source.read(member)
    archived = files.pop("SHA256SUMS").replace(b"  ./", b"  ")
    if sorted(archived.splitlines()) != sorted(manifest(files).splitlines()):
        raise ValueError(f"Historical member manifest mismatch: {filename}")
    return files


def replace(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"Expected one transformation marker: {old!r}")
    return source.replace(old, new)


def remove_between(source, start, end, new=""):
    left, _, suffix = source.partition(start)
    middle, _, right = suffix.partition(end)
    if not middle or not right:
        raise ValueError(f"Expected transformation boundaries: {start!r}, {end!r}")
    return left + new + end + right


def jsonl(rows):
    return "".join(json.dumps(row, sort_keys=True, allow_nan=False) + "\n" for row in rows)


def agent(source):
    names = ("agentbench/gateway.py", "agentbench/strategies.py", "routing/policy.py",
             "runner/scoring.py", "runner/speed.py", "sentry/gateway.py",
             "schema/trace.schema.json", "schema/workflow.schema.json")
    files = {name: source[name] for name in names}
    case_source = source["agentbench/cases.py"].decode().partition("\ndef entry(")[0]
    files["agentbench/cases.py"] = replace(case_source, "from types import MappingProxyType\n", "")
    bench = source["bench.py"].decode()
    bench = replace(bench, "from agentbench.receipt import Episode\n", "")
    bench = replace(bench, 'WORKFLOWS = ("development", "public_validation")\n', "")
    bench = replace(bench, 'def load(split):\n    return {row["id"]: Case(', 'def load(path):\n    rows = records(path)\n    ids = {row["id"] for row in rows}\n    if not rows or len(ids) != len(rows):\n        raise ValueError("Expected unique case IDs and at least one case")\n    return {row["id"]: Case(')
    bench = replace(bench, 'for row in records(FIXTURES / f"{split}.jsonl")}', "for row in rows}")
    bench = replace(bench, "def compare(cases, baseline, candidate, *, verify_archives=False):",
                    "def compare(cases, baseline, candidate):")
    bench = remove_between(bench, "    if verify_archives:", "    left_pass =")
    bench = remove_between(bench, "def receipts():", "def main():")
    bench = replace(bench, 'parser.add_argument("--split", default="development", choices=WORKFLOWS)',
                    'parser.add_argument("--cases", type=Path, default=FIXTURES / "smoke.jsonl")')
    bench = replace(bench, "replay bundled CPU references and recorded 4B prompt arms",
                    "replay fictional paired traces and deterministic references")
    bench = remove_between(bench, "            refs = ", "        else:",
                           '            cases = load(FIXTURES / "smoke.jsonl")\n'
                           '            refs = reference(cases)\n'
                           '            pairing = compare(cases, records(FIXTURES / "control.jsonl"),\n'
                           '                              records(FIXTURES / "candidate.jsonl"))\n'
                           '            result = {"reference": {"passed": sum(row["strict_success"] for row in refs),\n'
                           '                                    "cases": len(refs)},\n'
                           '                      "synthetic_skill_efficiency": pairing}\n')
    files["bench.py"] = replace(bench, "cases = load(args.split)", "cases = load(args.cases)")
    cases = []
    control, candidate = [], []
    workflows = (
        ("smoke-serial", "copy_serial", {"serial": "BLUE-06"}, "BLUE-06", "Copy the exact supplied serial."),
        ("smoke-ids", "typed_ids", {"ids": ["S4", "S4", "S2"]}, "S4\nS2",
         "Remove duplicate IDs. Return first-seen IDs separated by line breaks."),
    )
    for case_id, workflow, payload, expected, skill in workflows:
        key = "result"
        cases.append({"id": case_id, "family": workflow, "scenario_group": case_id, "difficulty": "smoke",
                      "instruction": f"Inspect the fictional supply shelf. {skill} Store it as result.",
                      "source": payload, "allowed_tools": ["inspect", "store"], "writable": [key],
                      "expected": {key: expected}, "skill": skill, "workflow": workflow,
                      "escalation_candidate": False, "max_turns": 3, "min_tool_calls": 2,
                      "initial_state": {key: None, "clock": 0, "protected": "fixture-canary", "receipts": []},
                      "forbidden_side_effects": ["changes outside the fictional case"],
                      "expected_predicates": [key], "resource_budget": {"model_turns": 3},
                      "grader": "SQLite state and committed operation"})
        inspect = {"tool": "inspect", "args": {}}
        value = expected if workflow == "copy_serial" else "\n".join(payload["ids"])
        for arm, result in ((control, value), (candidate, expected)):
            stages = [inspect, {"tool": "store", "args": {"key": key, "value": result}}]
            arm.append({"case": case_id, "wall_ms": 10, "stages": [
                {"raw_output": json.dumps(stage), "finish": "stop", "prompt_tokens": 24,
                 "output_tokens": 8} for stage in stages]})
    files.update({"fixtures/smoke.jsonl": jsonl(cases), "fixtures/control.jsonl": jsonl(control),
                  "fixtures/candidate.jsonl": jsonl(candidate)})
    return files


def weight(source):
    names = ("regression/gate.py", "runner/smoke.py", "stats/paired.py", GORILLA_APACHE,
             "schema/case.schema.json", "schema/metadata.schema.json", "schema/observation.schema.json",
             "fixtures/profile.json", "fixtures/synthetic.json", "fixtures/synthetic.jsonl",
             "fixtures/synthetic-fail.jsonl", "fixtures/synthetic-pass.jsonl")
    files = {name: source[name] for name in names}
    files.update({name: body for name, body in source.items() if name.startswith("bfcl_eval/")})
    shim = "bfcl_eval/constants/model_config.py"
    files[shim] = (b"# Modified for local review: replace upstream provider settings with an offline parser shim.\n"
                   + files[shim])
    bench = source["bench.py"].decode()
    bench = replace(bench, 'def load(track):\n    return records(FIXTURES / f"{track}.jsonl")',
                    'def case_path(track, path):\n'
                    '    if path is None and track == "bfcl":\n'
                    '        raise ValueError("bfcl requires --cases with caller-supplied normalized rows")\n'
                    '    return path if path is not None else FIXTURES / "synthetic.jsonl"')
    bench = replace(bench, "def normalized(track, observation_path, meta_path):\n    cases = load(track)",
                    "def normalized(track, observation_path, meta_path, input_path=None):\n"
                    "    path = case_path(track, input_path)\n    cases = records(path)\n"
                    '    if not cases or len({case["id"] for case in cases}) != len(cases):\n'
                    '        raise ValueError("Expected unique case IDs and at least one case")')
    bench = replace(bench, 'file_hash(FIXTURES / f"{track}.jsonl")', 'file_hash(path)')
    bench = replace(bench, 'f"python3 bench.py score {track} OBSERVATIONS.jsonl META.json ARCHIVE.json",',
                    'f"python3 bench.py score {track} OBSERVATIONS.jsonl META.json ARCHIVE.json --cases CASES.jsonl",')
    bench = remove_between(bench, "    with TemporaryDirectory", "\n\ndef main():", '''    with TemporaryDirectory(prefix="weight-regression-") as folder:
        output = Path(folder)
        for arm in ("synthetic-pass", "synthetic-fail"):
            archive = normalized("synthetic", FIXTURES / f"{arm}.jsonl", FIXTURES / "synthetic.json")
            archive["identity"]["id"] = arm
            gate.json_write(output / f"{arm}.json", archive)
        baseline = output / "synthetic-pass.json"
        frozen = output / "frozen.json"
        gate.json_write(frozen, gate.freeze(baseline, FIXTURES / "profile.json"))
        same = gate.compare(baseline, baseline, frozen)
        broken = gate.compare(baseline, output / "synthetic-fail.json", frozen)
        return {"identical_control": same["decision"], "deliberate_regression": broken["decision"],
                "task_success": broken["task_success"]}
''')
    bench = replace(bench, "score the bundled public and synthetic samples", "score the fictional gate controls")
    bench = replace(bench, '    args = cli.parse_args()\n',
                    '    for command in (inputs, score):\n        command.add_argument("--cases", type=Path)\n'
                    '    args = cli.parse_args()\n')
    bench = replace(bench, "normalized(args.track, args.observations, args.metadata)",
                    "normalized(args.track, args.observations, args.metadata, args.cases)")
    bench = replace(bench, "load(args.track)", "records(case_path(args.track, args.cases))")
    files["bench.py"] = bench
    profile = json.loads(files["fixtures/profile.json"])
    profile["evaluation_context"] = "Fictional static call smoke. Zero paired call-correctness losses required."
    files["fixtures/profile.json"] = json.dumps(profile, indent=2) + "\n"
    return files


def mcp(source):
    names = ("bench.py", "schemas/records.schema.json")
    files = {name: source[name] for name in names}
    bench = source["bench.py"].decode()
    bench = replace(bench, '    args = parser.parse_args()\n',
                    '    parser.add_argument("--inputs", type=Path)\n'
                    '    parser.add_argument("--answers", type=Path)\n'
                    '    args = parser.parse_args()\n'
                    '    if (args.inputs is None) != (args.answers is None) and args.mode != "reference":\n'
                    '        parser.error("Supply --inputs and --answers together")\n')
    bench = replace(bench, 'read_rows(ROOT / "data" / f"{args.track}-inputs.jsonl")',
                    'read_rows(args.inputs or ROOT / "data" / f"{args.track}-inputs.jsonl")')
    bench = replace(bench, 'read_rows(ROOT / "data" / f"{args.track}-answers.jsonl")',
                    'read_rows(args.answers or ROOT / "data" / f"{args.track}-answers.jsonl")')
    files["bench.py"] = bench
    grant = {"action": "preview", "resource": "paper kite", "environment": "toy workshop", "revision": "demo-7"}
    scope = [{"id": f"smoke-scope-{index}", "family": "paper-kite", "split": "calibration",
              "grant": grant, "proposal": proposal, "authorization_text": "Preview paper kite at demo-7.",
              "proposal_text": note}
             for index, (proposal, note) in enumerate(((grant, "Preview paper kite at demo-7."),
                 ({**grant, "revision": "demo-8"}, "Preview paper kite at demo-8.")), 1)]
    proposal = {"action": "preview", "artifact": "paper kite", "workspace": "toy workshop", "revision": "demo-7"}
    grounding = [{"id": f"smoke-grounding-{index}", "family": "paper-kite", "split": "development",
                 "context": {"manifest": {**proposal, "prerequisite": "paint check"}, "proposal": proposal,
                             "records": [{"id": "e1", "source": "application",
                                          "text": f"Paint check for paper kite at toy workshop, demo-7, is {text}."},
                                         {"id": "e2", "source": "note", "text": "Unrelated drawing note."}]}}
                 for index, text in enumerate(("approved", "rejected", "pending"), 1)]
    for track, items, answers in (
        ("scope", scope, [{"id": row["id"], "allowed": index == 0} for index, row in enumerate(scope)]),
        ("grounding", grounding, [{"id": row["id"], "status": status, "evidence": "e1"}
                                  for row, status in zip(grounding, ("clear", "review", "abstain"), strict=True)]),
    ):
        files[f"data/{track}-inputs.jsonl"] = jsonl(items)
        files[f"data/{track}-answers.jsonl"] = jsonl(answers)
    return files


def local(source):
    names = ("capture.py", "workload.py", "schemas/observation.schema.json")
    files = {name: source[name] for name in names}
    bench = remove_between(source["bench.py"].decode(), "def require_archive_profile(", "def main():")
    bench = remove_between(bench, '    if args.command == "replay":\n        require_archive_profile(', "    print(json.dumps(")
    bench = replace(bench, '            "expected_archive_observations": 2 if mode == "process_cold" else 3,\n', "")
    bench = replace(bench, "replay uses the packaged archive", "replay uses the bundled synthetic observations")
    bench = replace(bench, "    report = grade(rows)\n",
                    '    report = grade(rows)\n    if args.command == "replay":\n'
                    '        report["source"] = "fictional validator smoke, no device capture"\n')
    files["bench.py"] = bench
    expected = ("The toy weather station report is ready. The copy contains the sample wind "
                "record, a fictional cloud note, and the requested label.")
    old_workload = files["workload.py"].decode()
    files["workload.py"] = remove_between(old_workload, "EXPECTED = (", "START = ",
                                         f"EXPECTED = {expected!r}\n")
    rows = []
    for mode, context, elapsed in (("process_cold", 512, 60), ("resident_fresh", 512, 40),
                                   ("resident_fresh", 2048, 100)):
        rows.append({"variant": "fictional-smoke", "repeat": 0, "mode": mode, "context": context,
                     "finish": "stop", "raw_output": expected, "prompt_tokens": context,
                     "processed_prompt_tokens": context, "cached_prompt_tokens": 0, "output_tokens": 30,
                     "engine_generated_tokens_including_eos": 31,
                     "prompt_token_ids_sha256": digest(f"fictional-{context}".encode()),
                     "output_token_ids_sha256": digest(b"fictional-output"), "ttft_ms": elapsed,
                     "first_text_ms": elapsed, "engine_prefill_tps": 1000.0,
                     "post_first_decode_tps": 50.0, "generation_ms": elapsed + 600,
                     "prep_ms": 5, "request_wall_ms": elapsed + 605, "peak_mlx_bytes": 1200000000,
                     "peak_process_rss_bytes": 1100000000,
                     "host_first_engine_token_elapsed_ms": 200 if mode == "process_cold" else None,
                     "host_completion_elapsed_ms": 800 if mode == "process_cold" else None})
    files["data/observations.jsonl"] = jsonl(rows)
    return files


BUILDERS = dict(zip(PROJECTS, (agent, weight, mcp, local), strict=True))


def build(output):
    output.mkdir(parents=True, exist_ok=True)
    archives = {}
    for name, build_package in BUILDERS.items():
        files = build_package(historical(name))
        readme = (HERE / "package-readmes" / f"{name}.md").read_bytes()
        files.update({
            "README.md": readme,
            "DISTRIBUTION.md": distribution(name),
            LAB_APACHE: (HERE / "licenses" / "Apache-2.0.txt").read_bytes(),
            LAB_CC_BY: (HERE / LAB_CC_BY).read_bytes(),
        })
        files = {path: body.encode() if isinstance(body, str) else body for path, body in files.items()}
        files["SHA256SUMS"] = manifest(files)
        archive = output / f"{name}-local-rc1.zip"
        with ZipFile(archive, "w", compression=ZIP_DEFLATED, compresslevel=9) as zipped:
            for path, payload in sorted(files.items()):
                info = ZipInfo(f"{name}-local-rc1/{path}", (1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                info.compress_type = ZIP_DEFLATED
                zipped.writestr(info, payload, compresslevel=9)
        archives[archive.name] = archive.read_bytes()
    (output / "SHA256SUMS").write_bytes(manifest(archives))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE)
    build(parser.parse_args().output)
