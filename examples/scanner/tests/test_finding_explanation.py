"""Unlabeled software checks over inert scanner-shaped records."""

from dataclasses import asdict
import json

import pytest

from sentry.finding_explanation import (
    MAX_CANDIDATE_CHARS,
    MAX_FINDINGS,
    MAX_ITEMS,
    MAX_TEXT_CHARS,
    ReviewedExplanation,
    ReviewedFindingSet,
    deterministic_explanation,
    prepare_finding,
    summarize_review,
    validate_explanation,
)


FINDING_ID = "format-observation"
OBSERVED = "The sample record uses a compact display format."
WHY = "The displayed width controls the fixture comparison."
EVIDENCE = "The display width is 24."


@pytest.fixture
def report():
    return {
        "schemaVersion": 1,
        "kind": "source",
        "coverage": {"complete": False},
        "findings": [
            {
                "fingerprint": FINDING_ID,
                "ruleId": "sample-rule",
                "ruleVersion": "1.0",
                "title": "Display width observation",
                "severity": "low",
                "confidence": "medium",
                "evidenceType": "static-pattern",
                "locations": [
                    {"file": "examples/display.txt", "line": 42, "column": 4},
                    {"file": "examples/summary.txt", "line": 7, "pointer": "/display"},
                ],
                "observed": OBSERVED,
                "why": WHY,
                "evidence": EVIDENCE,
                "assumptions": ["The input describes a display fixture."],
                "limitations": ["The display was never opened."],
            }
        ],
    }


def candidate(*selections, **overrides):
    item = {
        "schema_version": 1,
        "finding_id": FINDING_ID,
        "decision": "explain",
        "clauses": [{"evidence_id": key, "text": text} for key, text in selections],
    }
    return json.dumps({**item, **overrides})


def test_baseline_and_model_keep_canonical_locations_and_context(report):
    finding = prepare_finding(report, FINDING_ID)
    baseline = deterministic_explanation(finding)
    model = validate_explanation(finding, candidate(("evidence", EVIDENCE), ("observed", OBSERVED)))

    assert baseline.status == model.status == "answered"
    assert model.evidence_ids_valid is model.clause_text_matches_scanner is True
    assert baseline.selected_clauses == finding.clauses
    assert [(item.evidence_id, item.text) for item in model.selected_clauses] == [
        ("observed", OBSERVED),
        ("evidence", EVIDENCE),
    ]
    assert baseline.scanner_context == model.scanner_context == finding.context
    assert [(location.file, location.line) for location in model.scanner_context.locations] == [
        ("examples/display.txt", 42),
        ("examples/summary.txt", 7),
    ]
    assert model.scanner_context.coverage_complete is False
    assert model.scanner_context.assumptions == ("The input describes a display fixture.",)
    assert model.scanner_context.limitations == ("The display was never opened.",)


def test_known_id_does_not_support_changed_or_transposed_text(report):
    finding = prepare_finding(report, FINDING_ID)
    for replacement in ("The width is 48.", WHY, OBSERVED + " It controls the page.", f" {OBSERVED}"):
        outcome = validate_explanation(finding, candidate(("observed", replacement)))

        assert outcome.status == "rejected"
        assert outcome.reason == "unsupported_claim"
        assert outcome.evidence_ids_valid is True
        assert outcome.clause_text_matches_scanner is False
        assert outcome.selected_clauses == ()
        assert replacement not in json.dumps(asdict(outcome))


@pytest.mark.parametrize("selections", [
    (("unknown", OBSERVED),),
    (("observed", OBSERVED), ("observed", OBSERVED)),
])
def test_unknown_or_repeated_ids_have_separate_diagnostic(report, selections):
    outcome = validate_explanation(prepare_finding(report, FINDING_ID), candidate(*selections))

    assert outcome.status == "rejected"
    assert outcome.reason == "invalid_evidence_ids"
    assert outcome.evidence_ids_valid is False
    assert outcome.clause_text_matches_scanner is None
    assert outcome.selected_clauses == ()


def test_rejects_cross_finding_citation_and_extra_location_fields(report):
    report["findings"].append({
        **report["findings"][0],
        "fingerprint": "second-finding",
        "observed": "The second record uses a different display.",
        "locations": [{"file": "examples/second.txt", "line": 18}],
    })
    finding = prepare_finding(report, FINDING_ID)
    second_id = validate_explanation(finding, candidate(("observed", OBSERVED), finding_id="second-finding"))
    wrong_quote = validate_explanation(
        finding, candidate(("observed", report["findings"][1]["observed"])),
    )
    extra_location = validate_explanation(
        finding, candidate(("observed", OBSERVED), location={"file": "examples/second.txt", "line": 18}),
    )
    extra_clause_location = validate_explanation(
        finding, candidate(clauses=[{"evidence_id": "observed", "text": OBSERVED, "line": 18}]),
    )

    assert [row.reason for row in (second_id, wrong_quote, extra_location, extra_clause_location)] == [
        "finding_id_mismatch", "unsupported_claim", "invalid_schema", "invalid_clauses",
    ]
    assert all(row.status == "rejected" and row.selected_clauses == () for row in
               (second_id, wrong_quote, extra_location, extra_clause_location))
    assert extra_location.scanner_context.locations[0].line == 42


@pytest.mark.parametrize("raw,reason", [
    (candidate(decision="abstain"), "model_abstention"),
    (candidate(("observed", OBSERVED), decision="abstain"), "abstention_with_claims"),
    (candidate(("why", WHY)), "missing_observation"),
    (candidate(), "invalid_clauses"),
    (candidate(("observed", OBSERVED), schema_version=True), "invalid_schema"),
    ('{"schema_version":1,"schema_version":1}', "invalid_payload"),
    (candidate(clauses=[]).replace('"clauses": []', '"clauses":[{"text":"a","text":"b"}]'), "invalid_payload"),
    ("extra text " + candidate(), "invalid_payload"),
    (" " * (MAX_CANDIDATE_CHARS + 1), "invalid_payload"),
    ("[" * 2000, "invalid_payload"),
])
def test_unanswered_outputs_release_no_model_clauses(report, raw, reason):
    outcome = validate_explanation(prepare_finding(report, FINDING_ID), raw)

    assert outcome.reason == reason
    assert outcome.status == ("abstained" if reason == "model_abstention" else "rejected")
    assert outcome.selected_clauses == ()


def test_only_a_file_and_line_on_the_same_location_are_citable(report):
    report["findings"][0]["locations"] = [
        {"file": "examples/display.txt"},
        {"line": 42},
        {"pointer": "/display"},
    ]
    finding = prepare_finding(report, FINDING_ID)
    baseline = deterministic_explanation(finding)
    model = validate_explanation(finding, candidate(("observed", OBSERVED)))

    assert baseline.status == model.status == "abstained"
    assert baseline.reason == model.reason == "missing_source_line"
    assert baseline.selected_clauses == model.selected_clauses == ()
    assert baseline.evidence_ids_valid is baseline.clause_text_matches_scanner is None
    assert model.evidence_ids_valid is model.clause_text_matches_scanner is True


def test_report_packet_is_a_copy_of_the_selected_finding(report):
    selected = prepare_finding(report, FINDING_ID)
    report["findings"][0]["observed"] = "The report was changed after packet creation."
    report["findings"][0]["locations"][0]["line"] = 400

    assert selected.clauses[0].text == OBSERVED
    assert selected.context.locations[0].line == 42


@pytest.mark.parametrize("field,value", [
    ("locations", [{"file": "examples/display.txt", "line": True}]),
    ("locations", [{"file": "examples/display.txt", "line": None}]),
    ("locations", [{"file": "examples/display.txt", "line": 0}]),
    ("locations", []),
    ("locations", [{"file": "examples/display.txt"}] * (MAX_ITEMS + 1)),
    ("observed", "x" * (MAX_TEXT_CHARS + 1)),
    ("observed", " "),
    ("evidenceType", "metadata-observation"),
    ("severity", None),
])
def test_invalid_or_excessive_scanner_fields_are_not_rendered(report, field, value):
    report["findings"][0][field] = value

    with pytest.raises(ValueError):
        prepare_finding(report, FINDING_ID)


def test_only_unique_fingerprints_from_source_reports_can_be_selected(report):
    with pytest.raises(ValueError, match="exactly one"):
        prepare_finding(report, "absent")
    with pytest.raises(ValueError, match="exactly one"):
        prepare_finding({**report, "findings": report["findings"] * 2}, FINDING_ID)
    with pytest.raises(ValueError, match="finding list"):
        prepare_finding({**report, "findings": report["findings"] * (MAX_FINDINGS + 1)}, FINDING_ID)
    with pytest.raises(ValueError, match="source report"):
        prepare_finding({**report, "kind": "diff"}, FINDING_ID)


def test_empty_review_uses_null_rates_without_inventing_judgments():
    summary = summarize_review([], [])

    assert summary["explanation_cases"] == summary["reviewed_reports"] == 0
    for name in (
        "answered_coverage",
        "valid_evidence_ids",
        "correct_citations",
        "supported_claims",
        "grounded_answer_coverage",
        "grounded_answer_coverage_lower_bound_all_eligible",
        "false_abstentions",
        "unanswered_on_answerable",
        "missed_scanner_findings",
        "false_scanner_findings",
        "missed_explainer_findings",
        "spurious_explainer_findings",
        "reports_with_spurious_attempts",
    ):
        assert summary[name] == {"count": 0, "scored": 0, "rate": None}


def test_blanket_abstention_gets_zero_answers_and_full_false_abstention():
    count_rows = [
        ReviewedExplanation(status="abstained", eligible=True, answerable=True),
        ReviewedExplanation(status="abstained", eligible=True, answerable=False),
        ReviewedExplanation(status="abstained", eligible=True, answerable=None),
    ]
    summary = summarize_review(count_rows, [])

    assert summary["attempted"] == summary["abstained"] == 3
    assert summary["answered_coverage"] == {"count": 0, "scored": 3, "rate": 0.0}
    assert summary["grounded_answer_coverage"] == {"count": 0, "scored": 1, "rate": 0.0}
    assert summary["grounded_answer_coverage_lower_bound_all_eligible"] == {"count": 0, "scored": 3, "rate": 0.0}
    assert summary["false_abstentions"] == {"count": 1, "scored": 1, "rate": 1.0}
    assert summary["supported_claims"]["rate"] is None


def test_review_keeps_denominators_separate_for_aggregate_algebra():
    count_rows = [
        ReviewedExplanation("answered", True, True, True, (True,), (True, False)),
        ReviewedExplanation("answered", True, True, True, (True,), (True,)),
        ReviewedExplanation("answered", True, True),
        ReviewedExplanation("rejected", True, True, False),
        ReviewedExplanation("not_attempted", True, True),
        ReviewedExplanation("answered", False, None, True, (False,), (False,)),
    ]
    finding_sets = [
        ReviewedFindingSet(
            frozenset({"a", "b", "c"}), frozenset({"a", "c", "d"}), frozenset({"a", "e"}),
            frozenset({"d", "e"}),
        ),
    ]
    summary = summarize_review(count_rows, finding_sets)

    assert summary["answered"] == 4
    assert summary["unreviewed_answers_on_answerable"] == 1
    assert summary["reviewer_confirmed_answerable"] == 5
    assert summary["answered_coverage"] == {"count": 3, "scored": 5, "rate": 0.6}
    assert summary["grounded_answer_coverage"] == {"count": 1, "scored": 4, "rate": 0.25}
    assert summary["grounded_answer_coverage_lower_bound_all_eligible"] == {"count": 1, "scored": 5, "rate": 0.2}
    assert summary["unanswered_on_answerable"] == {"count": 2, "scored": 5, "rate": 0.4}
    assert summary["valid_evidence_ids"]["count"] == 2
    assert summary["valid_evidence_ids"]["scored"] == 3
    assert summary["correct_citations"] == {"count": 2, "scored": 2, "rate": 1.0}
    assert summary["supported_claims"]["count"] == 2
    assert summary["supported_claims"]["scored"] == 3
    assert summary["missed_scanner_findings"]["scored"] == 3
    assert summary["false_scanner_findings"]["scored"] == 3
    assert summary["missed_scanner_findings"]["count"] == summary["false_scanner_findings"]["count"] == 1
    assert summary["missed_explainer_findings"] == {"count": 1, "scored": 2, "rate": 0.5}
    assert summary["spurious_explainer_findings"] == {"count": 1, "scored": 2, "rate": 0.5}
    assert summary["reports_with_spurious_attempts"] == {"count": 1, "scored": 1, "rate": 1.0}


def test_grounded_credit_requires_valid_ids_and_complete_independent_judgments():
    count_rows = [
        ReviewedExplanation("answered", True, True, False, (True,), (True,)),
        ReviewedExplanation("answered", True, True, None, (True,), (True,)),
        ReviewedExplanation("answered", True, True, None, (False,)),
        ReviewedExplanation("answered", True, True, True, (True,)),
        ReviewedExplanation("answered", True, True, True, (True,), (True,)),
        ReviewedExplanation("abstained", True, None),
    ]
    summary = summarize_review(count_rows, [])

    assert summary["unreviewed_answers_on_answerable"] == 2
    assert summary["grounded_answer_coverage"]["count"] == 1
    assert summary["grounded_answer_coverage"]["scored"] == 3
    assert summary["grounded_answer_coverage_lower_bound_all_eligible"]["count"] == 1
    assert summary["grounded_answer_coverage_lower_bound_all_eligible"]["scored"] == 6
