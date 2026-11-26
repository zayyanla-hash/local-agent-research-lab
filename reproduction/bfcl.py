"""Reproduce the four archived static Python BFCL categories with frozen local MLX weights."""
import argparse
from copy import deepcopy
import errno
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import re
from shutil import copyfile
import socket
import sys
from types import ModuleType, SimpleNamespace


PINS = json.loads(Path(__file__).with_name("pins.json").read_text(encoding="utf-8"))
CATEGORIES = ("simple_python", "multiple", "parallel", "parallel_multiple")
PROTOCOL = PINS["protocol"]
BFCL_COMPONENT = "berkeley-function-call-leaderboard"


def sha(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def verify_files(folder, expected):
    for name, pin in expected.items():
        path = folder / name
        if sha(path) != pin:
            raise ValueError(f"SHA-256 mismatch for {name}")
    return len(expected)


def jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def category_data(root, suite):
    filename = f"BFCL_v4_{suite}.json"
    data = root / "bfcl_eval/data"
    rows = jsonl(data / filename)
    answers = jsonl(data / "possible_answer" / filename)
    cases = []
    for row in rows:
        if len(row["question"]) != 1:
            raise ValueError("static comparison requires a single user turn")
        cases.append({"id": row["id"], "messages": row["question"][0],
                      "tools": [{"type": "function", "function": tool} for tool in row["function"]]})
    truth = {row["id"]: row["ground_truth"] for row in answers}
    expected = PINS["bfcl"]["categories"][suite]
    if len(cases) != len(answers) or len(cases) != expected["paired"] or set(truth) != {c["id"] for c in cases}:
        raise ValueError(f"{suite}: case and answer inventories differ")
    if digest(cases) != expected["case_digest"]:
        raise ValueError(f"{suite}: prepared cases differ from the archived prompt/schema/order digest")
    return rows, cases, truth


def official_checker(root):
    # The pinned AST scorer uses one model-registry flag for function-name normalization.
    # Supply the same local entry as the historical harness, without provider imports.
    sys.path.insert(0, str(root))
    module = ModuleType("bfcl_eval.constants.model_config")
    module.MODEL_CONFIG_MAPPING = {"local-qwen": SimpleNamespace(underscore_to_dot=False)}
    sys.modules[module.__name__] = module
    from bfcl_eval.constants.enums import Language
    from bfcl_eval.eval_checker.ast_eval.ast_checker import ast_checker
    return ast_checker, Language.PYTHON


def parse_native(text, tokenizer, tools):
    fragments = re.findall(r"<tool_call>(.*?)</tool_call>", text, flags=re.DOTALL)
    calls, errors = [], []
    if text.count("<tool_call>") != len(fragments):
        errors.append("unclosed_tool_call")
    for fragment in fragments:
        try:
            item = tokenizer.tool_parser(fragment, tools)
            if not isinstance(item.get("name"), str) or not isinstance(item.get("arguments"), dict):
                raise ValueError("invalid call fields")
            calls.append({item["name"]: item["arguments"]})
        except (TypeError, AttributeError, KeyError, OverflowError, ValueError, SyntaxError) as exc:
            errors.append(type(exc).__name__)
    return calls, errors


def grade_case(checker, language, suite, description, truth, calls, errors):
    if errors or not calls:
        return False, "ast_decoder:decoder_failed"
    # Grading each arm starts from the same source values even if the scorer mutates a nested object.
    grade = checker(deepcopy(description), deepcopy(calls), deepcopy(truth), language, suite, "local-qwen")
    return grade["valid"], grade.get("error_type") if not grade["valid"] else None


def render_prompt(tokenizer, case):
    text = tokenizer.apply_chat_template(case["messages"], tools=case["tools"], tokenize=False,
                                         add_generation_prompt=True, enable_thinking=PROTOCOL["thinking"])
    return tokenizer.encode(text, add_special_tokens=False)


def infer_batch(model, tokenizer, cases):
    import mlx.core as mx
    from mlx_lm.generate import BatchGenerator

    inputs = [render_prompt(tokenizer, row) for row in cases]
    mx.random.seed(PROTOCOL["seed"])
    generator = BatchGenerator(model, stop_tokens=[[token] for token in tokenizer.eos_token_ids],
                               completion_batch_size=len(cases), prefill_batch_size=len(cases))
    try:
        uids = generator.insert(inputs, [PROTOCOL["generation_cap"]] * len(inputs))
        tokens = {uid: [] for uid in uids}
        while responses := generator.next_generated():
            for item in responses:
                if item.finish_reason != "stop":
                    tokens[item.uid].append(item.token)
        return [parse_native(tokenizer.decode(tokens[uid], skip_special_tokens=False), tokenizer, case["tools"])
                for uid, case in zip(uids, cases, strict=True)]
    finally:
        generator.close()


def assert_offline():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(1)
        try:
            probe.connect(("127.0.0.1", 9))
        except OSError as exc:
            if exc.errno in (errno.EPERM, errno.EACCES):
                return
            raise ValueError("Run this command with the documented network-denied sandbox") from exc
    raise ValueError("Network probe unexpectedly succeeded")


def check_runtime():
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1")
    for name in ("mlx", "mlx-lm", "transformers"):
        actual = version(name)
        if actual != PROTOCOL[name]:
            raise ValueError(f"{name} {actual} does not match the frozen runtime {PROTOCOL[name]}")


def run_arm(model_path, source, checker, language, suites):
    from mlx_lm import load

    model, tokenizer = load(str(model_path.resolve(strict=True)),
                            tokenizer_config={"trust_remote_code": False, "local_files_only": True})
    scores = {}
    for suite in suites:
        rows, cases, truth = category_data(source, suite)
        scores[suite] = []
        for offset in range(0, len(cases), PROTOCOL["batch_size"]):
            batch = cases[offset:offset + PROTOCOL["batch_size"]]
            calls_and_errors = infer_batch(model, tokenizer, batch)
            for row, (calls, errors) in zip(rows[offset:offset + len(batch)], calls_and_errors, strict=True):
                correct, _ = grade_case(checker, language, suite, row["function"], truth[row["id"]], calls, errors)
                scores[suite].append(correct)
    return scores


def derive_base(source, target):
    assert_offline()
    check_runtime()
    files = PINS["models"]["upstream"]["verified_files"]
    verify_files(source, files)
    if target.exists():
        raise ValueError("derive-base requires a new destination")
    from mlx_lm.convert import convert

    convert(str(source.resolve()), str(target.resolve()), quantize=True, q_group_size=64, q_bits=4,
            q_mode="affine", dtype="bfloat16", trust_remote_code=False)
    copyfile(source / "LICENSE", target / "LICENSE")
    return {"parent": verify_files(target, PINS["models"]["parent"])}


def summarize(parent, step12, suites):
    summary = {}
    for suite in suites:
        before, after = parent[suite], step12[suite]
        summary[suite] = {"paired": len(before), "parent_correct": sum(before), "step12_correct": sum(after),
                          "rescued": sum(not a and b for a, b in zip(before, after, strict=True)),
                          "lost": sum(a and not b for a, b in zip(before, after, strict=True))}
    counts = {key: sum(row[key] for row in summary.values()) for key in next(iter(summary.values()))}
    return {"categories": summary, "pooled_descriptive_counts": counts, "protocol": PROTOCOL}


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    sub = cli.add_subparsers(dest="command", required=True)
    for name in ("verify", "run"):
        mode = sub.add_parser(name)
        for field in ("bfcl", "parent", "step12"):
            mode.add_argument(f"--{field}", type=Path, required=True)
        if name == "run":
            mode.add_argument("--suite", choices=CATEGORIES, action="append", required=True)
    derive = sub.add_parser("derive-base")
    derive.add_argument("source", type=Path)
    derive.add_argument("output", type=Path)
    args = cli.parse_args()
    try:
        if args.command == "derive-base":
            report = derive_base(args.source, args.output)
        else:
            source = (args.bfcl / BFCL_COMPONENT).resolve(strict=True)
            verified = verify_files(source, PINS["bfcl"]["verified_files"])
            assets = {arm: verify_files(getattr(args, arm), PINS["models"][arm]) for arm in ("parent", "step12")}
            if args.command == "verify":
                report = {"source_files_verified": verified, "model_files_verified": assets,
                          "prepared_case_counts": {suite: len(category_data(source, suite)[1]) for suite in CATEGORIES}}
            else:
                assert_offline()
                check_runtime()
                if len(args.suite) != len(set(args.suite)):
                    raise ValueError("select each suite only once")
                checker, language = official_checker(source)
                parent = run_arm(args.parent, source, checker, language, args.suite)
                step12 = run_arm(args.step12, source, checker, language, args.suite)
                report = summarize(parent, step12, args.suite)
        print(json.dumps(report, indent=2, allow_nan=False))
    except (KeyError, OSError, TypeError, ValueError) as exc:
        cli.error(str(exc))


if __name__ == "__main__":
    main()
