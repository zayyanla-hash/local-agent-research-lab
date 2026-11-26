"""Verify arithmetic of published paired outcome cells using Python's standard library."""

import json
from pathlib import Path


def grade(groups):
    fields = {"both_correct", "candidate_only", "parent_only", "both_wrong"}
    totals = dict.fromkeys(fields, 0)
    for name, row in groups.items():
        if set(row) != fields or any(type(v) is not int or v < 0 for v in row.values()):
            raise ValueError(f"Invalid paired outcome counts for {name}")
        for key in fields:
            totals[key] += row[key]
    n = sum(totals.values())
    if n == 0:
        raise ValueError("Empty cohort")
    return {
        "cases": n,
        "parent_correct": totals["both_correct"] + totals["parent_only"],
        "candidate_correct": totals["both_correct"] + totals["candidate_only"],
        "gains": totals["candidate_only"],
        "losses": totals["parent_only"],
        "difference_pp": round(
            100 * (totals["candidate_only"] - totals["parent_only"]) / n, 6
        ),
    }


def verify(receipt):
    expected = {
        "weightforge": (
            {
                "simple_python": 400,
                "multiple": 200,
                "parallel": 200,
                "parallel_multiple": 200,
            },
            (1000, 699, 793, 101, 7),
        ),
        "sentry": ({"alarm": 80, "media": 152}, (232, 135, 158, 43, 20)),
    }
    result = {}
    for name, (sizes, headline) in expected.items():
        groups = receipt[name]["groups"]
        if {k: sum(v.values()) for k, v in groups.items()} != sizes:
            raise ValueError(f"Unexpected {name} cohort")
        scores = grade(groups)
        fields = ("cases", "parent_correct", "candidate_correct", "gains", "losses")
        if tuple(scores[k] for k in fields) != headline:
            raise ValueError(f"{name} paired cells disagree with published claim")
        result[name] = scores
    for arm, key in (
        ("parent-fewshot", "parent_correct"),
        ("rank4-fewshot", "candidate_correct"),
    ):
        record = receipt["sentry"]["logit_files"][arm]
        if (record["n"], record["correct"]) != (
            result["sentry"]["cases"],
            result["sentry"][key],
        ):
            raise ValueError(f"Inconsistent Sentry trace summary for {arm}")
    parity = receipt["staged_parity"]
    joint = parity[
        "sentry_packaged_resolver_renderer_joint_correct_using_archived_logits"
    ]
    if (
        joint != {"parent-fewshot": 135, "rank4-fewshot": 158}
        or parity["sentry_development_model_visible_message_lists_identical"] != 232
    ):
        raise ValueError("Unexpected packaged-assessor parity")
    return result


if __name__ == "__main__":
    path = Path(__file__).resolve().with_name("replay-aggregates.json")
    print(json.dumps(verify(json.loads(path.read_text())), indent=2))
