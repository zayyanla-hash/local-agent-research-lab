"""Audit historical and proposed ZIP members and replay the proposed candidates offline."""
import argparse
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from build import (
    AGENT, FIXTURE_DATA, GORILLA_APACHE, HERE, HISTORY, LAB_APACHE, LAB_CC_BY, LOCAL,
    MCP, PROJECTS, WEIGHT, digest, distribution, historical, manifest,
)

PERSONAL = re.compile(r"(?i)(?:/(?:Users|home|Volumes)/[\w.-]+/|[A-Z]:\\Users\\[\w.-]+\\)")
CREDENTIAL = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----|(?:hf_|ghp_|sk-proj-)[A-Za-z0-9_-]{20,}")
FILE_TYPES = {".md", ".py", ".json", ".jsonl", ".txt"}
DISTRIBUTION_STATUS = "publication approved"


def checked_members(path, *, draft):
    result = {}
    permissions = set()
    with ZipFile(path) as archive:
        if error := archive.testzip():
            raise ValueError(f"Failed archive CRC: {error}")
        for info in archive.infolist():
            raw_parts = info.filename.split("/")
            member = PurePosixPath(info.filename)
            if (member.is_absolute() or "\\" in info.filename or any(
                    not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", part) for part in raw_parts)
                    or raw_parts[0] != path.stem or len(raw_parts) < 2):
                raise ValueError(f"Unsafe archive member name: {info.filename}")
            name = "/".join(raw_parts[1:])
            if name.casefold() in result:
                raise ValueError(f"Duplicate archive member: {name}")
            mode = info.external_attr >> 16
            if not stat.S_ISREG(mode) or mode & 0o7000 or (draft and mode != 0o100644):
                raise ValueError(f"Unsafe archive member mode: {name}: {oct(mode)}")
            permissions.add(oct(stat.S_IMODE(mode)))
            if ((member.suffix not in FILE_TYPES and member.name not in {"LICENSE", "SHA256SUMS"})
                    or info.file_size > 2_000_000 or info.flag_bits & 1 or info.extra or info.comment):
                raise ValueError(f"Unexpected archive member metadata: {name}")
            body = archive.read(info)
            value = body.decode("utf-8")
            if "\x00" in value or PERSONAL.search(value) or CREDENTIAL.search(value):
                raise ValueError(f"Review required for a local path or credential marker in {name}")
            if member.suffix == ".json":
                json.loads(value)
            if member.suffix == ".jsonl":
                for line in value.splitlines():
                    json.loads(line)
            result[name.casefold()] = (name, body)
        if archive.comment:
            raise ValueError(f"Unexpected archive comment: {path.name}")
    members = dict(result.values())
    contents = {name: body for name, body in members.items() if name != "SHA256SUMS"}
    expected = members["SHA256SUMS"].replace(b"  ./", b"  ")
    if sorted(expected.splitlines()) != sorted(manifest(contents).splitlines()):
        raise ValueError(f"Archive member hashes disagree: {path.name}")
    return members, sorted(permissions)


def verify_license_and_fixtures(project, files):
    data = set(FIXTURE_DATA[project])
    observed = {path for path in files if path.endswith(".jsonl")}
    if observed != data:
        raise ValueError(f"Unexpected fixture inventory: {project}: {sorted(observed ^ data)}")
    expected = {
        "DISTRIBUTION.md": distribution(project).encode(),
        LAB_APACHE: (HERE / "licenses" / "Apache-2.0.txt").read_bytes(),
        LAB_CC_BY: (HERE / LAB_CC_BY).read_bytes(),
    }
    for path, body in expected.items():
        if files.get(path) != body:
            raise ValueError(f"License or scoped notice differs: {project}: {path}")
    if project == WEIGHT and digest(files[GORILLA_APACHE]) != (
            "c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4"):
        raise ValueError("Pinned Gorilla license changed")
    return sorted(data)


def run(root, sandbox, *args, expected=0):
    proc = subprocess.run([*sandbox, *args], cwd=root, capture_output=True, check=False, timeout=15,
                          env={"PATH": "/opt/homebrew/bin:/usr/bin:/bin", "LANG": "C.UTF-8",
                               "PYTHONDONTWRITEBYTECODE": "1"})
    if proc.returncode != expected:
        raise ValueError(f"Unexpected status {proc.returncode} for {args}: {proc.stderr.decode()}")
    return proc.stdout.decode()


def smoke(project, root, sandbox):
    run(root, sandbox[:3], "/usr/bin/shasum", "-a", "256", "-c", "SHA256SUMS")
    command = ("bench.py",)
    if project == AGENT:
        summary = json.loads(run(root, sandbox, *command, "sample"))
        pairing = summary["synthetic_skill_efficiency"]
        direct = json.loads(run(root, sandbox, *command, "skill", "fixtures/control.jsonl",
                                "fixtures/candidate.jsonl", "--cases", "fixtures/smoke.jsonl"))
        assert summary["reference"] == {"passed": 2, "cases": 2} and pairing == direct
        assert pairing["baseline"]["strict_successes"] == 1 and pairing["skill"]["strict_successes"] == 2
        assert pairing["resolved"] == ["smoke-ids"] and pairing["new_failures"] == []
        return {"reference_strict": [2, 2], "control_strict": [1, 2], "candidate_strict": [2, 2]}
    if project == WEIGHT:
        summary = json.loads(run(root, sandbox, *command, "sample"))
        assert summary["identical_control"] == "pass" and summary["deliberate_regression"] == "regression"
        run(root, sandbox, *command, "cases", "bfcl", expected=2)
        selected = json.loads(run(root, sandbox, *command, "cases", "bfcl",
                                  "--cases", "fixtures/synthetic.jsonl"))
        assert len(selected) == 6 and all("ground_truth" not in row for row in selected)
        for arm in ("synthetic-pass", "synthetic-fail"):
            run(root, sandbox, *command, "score", "bfcl", f"fixtures/{arm}.jsonl",
                "fixtures/synthetic.json", f"{arm}.json", "--cases", "fixtures/synthetic.jsonl")
        run(root, sandbox, "-m", "regression.gate", "freeze", "synthetic-pass.json", "fixtures/profile.json",
            "frozen.json")
        run(root, sandbox, "-m", "regression.gate", "compare", "synthetic-pass.json", "synthetic-fail.json",
            "frozen.json", "--output", "report.json", expected=1)
        report = json.loads((root / "report.json").read_text())
        assert report["decision"] == "regression"
        return {"fictional_cases": 6, "identical_control": "pass", "deliberate_regression": "regression",
                "missing_external_input_exit": 2, "caller_supplied_normalized_import": True}
    if project == MCP:
        scope = json.loads(run(root, sandbox, *command, "check", "--track", "scope"))["scored_fields"]["calibration"]
        grounding = json.loads(run(root, sandbox, *command, "check", "--track", "grounding"))["scored_fields"]["development"]
        assert scope["exact"] == scope["records"] == 2 and scope["denied_cases"] == 1
        assert grounding["joint_exact"] == grounding["records"] == 3 and grounding["correct_abstention"] == 1
        direct = json.loads(run(root, sandbox, *command, "grade", "--track", "grounding",
                                "--inputs", "data/grounding-inputs.jsonl", "--answers", "data/grounding-answers.jsonl",
                                "--predictions", "data/grounding-answers.jsonl"))
        assert direct["scored_fields"]["development"] == grounding
        return {"scope_exact": [2, 2], "grounding_joint_exact": [3, 3], "caller_supplied_case_and_answer_import": True}
    if project == LOCAL:
        summary = json.loads(run(root, sandbox, *command, "replay"))
        graded = json.loads(run(root, sandbox, *command, "grade", "--observations", "data/observations.jsonl"))
        assert summary.pop("source").startswith("fictional") and summary == graded
        groups = summary["variants"]["fictional-smoke"]
        assert len(groups) == 3 and all(row["exact"] == row["observations"] == 1 for row in groups.values())
        run(root, sandbox, "capture.py", "--help")
        return {"fictional_exact": [3, 3], "cold_and_resident_groups": 3, "capture_cli_help": True}
    raise ValueError(f"Unrecognized project: {project}")


def verify(folder, *, check_historical=True):
    expected_names = {f"{project}-local-rc1.zip" for project in PROJECTS}
    observed_names = {path.name for path in folder.glob("*.zip")}
    if expected_names != observed_names:
        raise ValueError(f"Unexpected archive inventory: {sorted(expected_names ^ observed_names)}")
    archives = {}
    for project in PROJECTS:
        path = folder / f"{project}-local-rc1.zip"
        archives[path.name] = path.read_bytes()
    if (folder / "SHA256SUMS").read_bytes() != manifest(archives):
        raise ValueError("Proposed ZIP checksums differ")
    records = {}
    with TemporaryDirectory(prefix="bench-candidate-verify-", dir="/tmp") as directory:
        base = Path(directory).resolve()
        profile = ('(version 1)(allow default)(deny network*)'
                   f'(deny file-read* (subpath "{Path.home()}"))'
                   f'(deny file-write*)(allow file-write* (subpath "{base}"))')
        sandbox = ("/usr/bin/sandbox-exec", "-p", profile, sys.executable, "-B", "-S")
        run(base, sandbox, "-c", "import errno,socket; "
            "s=socket.socket(); assert s.connect_ex(('127.0.0.1', 9)) in {errno.EPERM,errno.EACCES}")
        for project in PROJECTS:
            path = folder / f"{project}-local-rc1.zip"
            original_path = HISTORY / f"{project}.zip"
            files, new_modes = checked_members(path, draft=True)
            licensed_data = verify_license_and_fixtures(project, files)
            root = base / project
            for name, body in files.items():
                output = root / name
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(body)
            results = smoke(project, root, sandbox)
            records[project] = {
                "proposed_filename": path.name, "proposed_sha256": digest(archives[path.name]),
                "proposed_members": len(files), "proposed_modes": new_modes, "offline_smoke": results,
                "original_synthetic_data_cc_by_4_0": licensed_data,
                "original_software_license_sha256": digest(files[LAB_APACHE]),
                "synthetic_data_license_sha256": digest(files[LAB_CC_BY]),
            }
            if check_historical:
                historical(project)
                original, old_modes = checked_members(original_path, draft=False)
                records[project].update({
                    "historical_filename": original_path.name,
                    "historical_sha256": digest(original_path.read_bytes()),
                    "historical_members": len(original), "historical_modes": old_modes,
                    "historical_members_removed": sorted(original.keys() - files.keys()),
                    "historical_members_replaced": sorted(name for name in original.keys() & files.keys()
                                                          if original[name] != files[name]),
                })
    return {"distribution": DISTRIBUTION_STATUS,
            "licensor": "Zayyan Latif", "original_software_license": "Apache-2.0",
            "original_synthetic_data_license": "CC-BY-4.0", "network_probe": "blocked",
            "archive_checks": ["sha256", "per-member sha256", "CRC", "member type and mode",
                               "safe relative paths", "UTF-8 and JSON syntax", "local path and credential markers",
                               "scoped license notices and texts", "exact allowed JSONL fixture inventory"],
            "packages": records}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=Path, default=HERE)
    parser.add_argument("--staged-only", action="store_true", help="Verify the publication ZIPs without private history")
    arguments = parser.parse_args()
    print(json.dumps(verify(arguments.folder, check_historical=not arguments.staged_only), indent=2, sort_keys=True))
