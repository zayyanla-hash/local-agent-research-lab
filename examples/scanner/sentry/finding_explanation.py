"""Render validated selections over an existing MCP Guard static source report."""

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
import json
from typing import Literal


MAX_FINDINGS = 1000
MAX_ITEMS = 32
MAX_TEXT_CHARS = 2048
MAX_CANDIDATE_CHARS = 48 * 1024
SELECTABLE_FIELDS = ("observed", "why", "evidence")
ExplanationStatus = Literal["answered", "abstained", "rejected", "not_attempted"]


@dataclass(frozen=True)
class SourceLocation:
    file: str | None
    line: int | None
    column: int | None
    pointer: str | None


@dataclass(frozen=True)
class Clause:
    evidence_id: str
    text: str


@dataclass(frozen=True)
class FindingContext:
    finding_id: str
    rule_id: str
    rule_version: str
    title: str
    severity: str
    confidence: str
    coverage_complete: bool
    locations: tuple[SourceLocation, ...]
    assumptions: tuple[str, ...]
    limitations: tuple[str, ...]

    @property
    def locally_citable(self) -> bool:
        return any(location.file is not None and location.line is not None for location in self.locations)


@dataclass(frozen=True)
class FindingPacket:
    context: FindingContext
    clauses: tuple[Clause, ...]


@dataclass(frozen=True)
class Explanation:
    scanner_context: FindingContext
    status: ExplanationStatus
    reason: str
    selected_clauses: tuple[Clause, ...] = ()
    evidence_ids_valid: bool | None = None
    clause_text_matches_scanner: bool | None = None


@dataclass(frozen=True)
class ReviewedExplanation:
    """Aggregate inputs with eligibility, answerability and accuracy from the reviewer."""

    status: ExplanationStatus
    eligible: bool
    answerable: bool | None
    evidence_ids_valid: bool | None = None
    citations_correct: tuple[bool, ...] | None = None
    claims_supported: tuple[bool, ...] | None = None


@dataclass(frozen=True)
class ReviewedFindingSet:
    """One report's reconciled finding IDs on the independent scorer's identity scheme."""

    expected: frozenset[str]
    scanner: frozenset[str]
    explained: frozenset[str]
    spurious_attempts: frozenset[str] = frozenset()


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _text(value):
    _require(
        type(value) is str and 0 < len(value) <= MAX_TEXT_CHARS and bool(value.strip()),
        "Expected nonempty bounded scanner text.",
    )
    return value


def _number(value):
    _require(type(value) is int and 1 <= value <= 2**53 - 1, "Invalid scanner source coordinate.")
    return value


def _location(value):
    _require(type(value) is dict and 0 < len(value) <= 4, "Invalid scanner location.")
    _require(set(value) <= {"file", "line", "column", "pointer"}, "Invalid scanner location fields.")
    return SourceLocation(
        file=_text(value["file"]) if "file" in value else None,
        line=_number(value["line"]) if "line" in value else None,
        column=_number(value["column"]) if "column" in value else None,
        pointer=_text(value["pointer"]) if "pointer" in value else None,
    )


def _items(value, *, minimum=0):
    _require(type(value) is list and minimum <= len(value) <= MAX_ITEMS, "Invalid scanner list.")
    return value


def prepare_finding(report: dict, finding_id: str) -> FindingPacket:
    """Copy a uniquely identified source finding from an authenticated scanner report."""
    _text(finding_id)
    _require(
        type(report) is dict and type(report.get("schemaVersion")) is int
        and report["schemaVersion"] == 1 and report.get("kind") == "source",
        "Expected an MCP Guard v1 source report.",
    )
    findings = report.get("findings")
    _require(type(findings) is list and len(findings) <= MAX_FINDINGS, "Invalid scanner finding list.")
    _require(all(type(finding) is dict for finding in findings), "Invalid scanner finding.")
    matching = [finding for finding in findings if finding.get("fingerprint") == finding_id]
    _require(len(matching) == 1, "Finding fingerprint must match exactly one scanner finding.")
    finding = matching[0]

    coverage = report.get("coverage")
    _require(type(coverage) is dict and type(coverage.get("complete")) is bool, "Invalid coverage.")
    _require(finding.get("evidenceType") == "static-pattern", "Expected a static source finding.")
    _require(finding.get("severity") in ("low", "medium", "high"), "Invalid scanner severity.")
    _require(finding.get("confidence") in ("medium", "high"), "Invalid scanner confidence.")
    context = FindingContext(
        finding_id=finding_id,
        rule_id=_text(finding.get("ruleId")),
        rule_version=_text(finding.get("ruleVersion")),
        title=_text(finding.get("title")),
        severity=finding["severity"],
        confidence=finding["confidence"],
        coverage_complete=coverage["complete"],
        locations=tuple(_location(item) for item in _items(finding.get("locations"), minimum=1)),
        assumptions=tuple(_text(item) for item in _items(finding.get("assumptions"))),
        limitations=tuple(_text(item) for item in _items(finding.get("limitations"))),
    )
    return FindingPacket(context, tuple(Clause(field, _text(finding.get(field))) for field in SELECTABLE_FIELDS))


def deterministic_explanation(finding: FindingPacket) -> Explanation:
    """Use the scanner's full observed, rationale and evidence fields."""
    context = finding.context
    if not context.locally_citable:
        return Explanation(context, "abstained", "missing_source_line")
    return Explanation(context, "answered", "scanner_report", finding.clauses, True, True)


def _unique_keys(pairs):
    values = {}
    for key, value in pairs:
        if key in values:
            raise ValueError("Duplicate JSON key.")
        values[key] = value
    return values


def validate_explanation(finding: FindingPacket, raw: str) -> Explanation:
    """Use model output only as a selection of exact, finding-scoped scanner clauses."""
    context = finding.context
    if type(raw) is not str or len(raw) > MAX_CANDIDATE_CHARS:
        return Explanation(context, "rejected", "invalid_payload")
    try:
        candidate = json.loads(raw, object_pairs_hook=_unique_keys)
    except (ValueError, RecursionError):
        return Explanation(context, "rejected", "invalid_payload")

    if (
        type(candidate) is not dict
        or set(candidate) != {"schema_version", "finding_id", "decision", "clauses"}
        or type(candidate["schema_version"]) is not int
        or candidate["schema_version"] != 1
        or candidate["decision"] not in ("explain", "abstain")
        or type(candidate["clauses"]) is not list
    ):
        return Explanation(context, "rejected", "invalid_schema")
    if candidate["finding_id"] != context.finding_id:
        return Explanation(context, "rejected", "finding_id_mismatch")

    proposed = candidate["clauses"]
    if candidate["decision"] == "abstain":
        if proposed:
            return Explanation(context, "rejected", "abstention_with_claims")
        return Explanation(context, "abstained", "model_abstention")
    if not 1 <= len(proposed) <= len(finding.clauses) or any(
        type(entry) is not dict or set(entry) != {"evidence_id", "text"}
        or type(entry["evidence_id"]) is not str or type(entry["text"]) is not str
        for entry in proposed
    ):
        return Explanation(context, "rejected", "invalid_clauses")

    accepted = {clause.evidence_id: clause.text for clause in finding.clauses}
    proposed_ids = [entry["evidence_id"] for entry in proposed]
    if len(set(proposed_ids)) != len(proposed_ids) or any(ref not in accepted for ref in proposed_ids):
        return Explanation(context, "rejected", "invalid_evidence_ids", evidence_ids_valid=False)
    if any(entry["text"] != accepted[entry["evidence_id"]] for entry in proposed):
        return Explanation(context, "rejected", "unsupported_claim", evidence_ids_valid=True,
                           clause_text_matches_scanner=False)
    if "observed" not in proposed_ids:
        return Explanation(context, "rejected", "missing_observation", evidence_ids_valid=True,
                           clause_text_matches_scanner=True)
    if not context.locally_citable:
        return Explanation(context, "abstained", "missing_source_line", evidence_ids_valid=True,
                           clause_text_matches_scanner=True)

    selected = tuple(clause for clause in finding.clauses if clause.evidence_id in proposed_ids)
    return Explanation(context, "answered", "validated_selection", selected, True, True)


def _rate(count: int, scored: int) -> dict:
    return {"count": count, "scored": scored, "rate": count / scored if scored else None}


def summarize_review(
    explanations: Iterable[ReviewedExplanation],
    finding_sets: Iterable[ReviewedFindingSet],
) -> dict:
    """Return counts only, using separately supplied judgments for semantic metrics."""
    statuses = Counter()
    eligible = eligible_answers = answerable = false_abstentions = unanswered_answerable = unreviewed_answers = 0
    id_checks, citations, claims, grounded_answers = [], [], [], []
    for row in explanations:
        _require(row.status in ("answered", "rejected", "abstained", "not_attempted"), "Unknown review status.")
        statuses[row.status] += 1
        if not row.eligible:
            continue
        eligible += 1
        if row.evidence_ids_valid is not None and row.status != "not_attempted":
            id_checks.append(row.evidence_ids_valid)
        if row.status == "answered":
            eligible_answers += 1
            citations.extend(row.citations_correct or ())
            claims.extend(row.claims_supported or ())
        if row.answerable is not True:
            continue
        answerable += 1
        if row.status != "answered":
            unanswered_answerable += 1
            false_abstentions += row.status == "abstained"
            grounded_answers.append(False)
        elif (
            row.evidence_ids_valid is False
            or False in (row.citations_correct or ())
            or False in (row.claims_supported or ())
        ):
            grounded_answers.append(False)
        elif row.evidence_ids_valid is True and row.citations_correct and row.claims_supported:
            grounded_answers.append(True)
        else:
            unreviewed_answers += 1

    findings = Counter()
    for row in finding_sets:
        findings["reports"] += 1
        findings["expected"] += len(row.expected)
        findings["scanner"] += len(row.scanner)
        findings["explained"] += len(row.explained)
        findings["scanner_missed"] += len(row.expected - row.scanner)
        findings["scanner_false"] += len(row.scanner - row.expected)
        findings["expected_in_report"] += len(row.expected & row.scanner)
        findings["explainer_missed"] += len((row.expected & row.scanner) - row.explained)
        findings["explainer_spurious"] += len(row.explained - row.scanner)
        findings["reports_with_spurious_attempts"] += bool(row.spurious_attempts - row.scanner)

    return {
        "explanation_cases": sum(statuses.values()),
        "eligible": eligible,
        "attempted": sum(statuses.values()) - statuses["not_attempted"],
        "answered": statuses["answered"],
        "rejected": statuses["rejected"],
        "abstained": statuses["abstained"],
        "not_attempted": statuses["not_attempted"],
        "reviewer_confirmed_answerable": answerable,
        "unreviewed_answers_on_answerable": unreviewed_answers,
        "answered_coverage": _rate(eligible_answers, eligible),
        "valid_evidence_ids": _rate(sum(id_checks), len(id_checks)),
        "correct_citations": _rate(sum(citations), len(citations)),
        "supported_claims": _rate(sum(claims), len(claims)),
        "grounded_answer_coverage": _rate(sum(grounded_answers), len(grounded_answers)),
        "grounded_answer_coverage_lower_bound_all_eligible": _rate(sum(grounded_answers), eligible),
        "false_abstentions": _rate(false_abstentions, answerable),
        "unanswered_on_answerable": _rate(unanswered_answerable, answerable),
        "reviewed_reports": findings["reports"],
        "missed_scanner_findings": _rate(findings["scanner_missed"], findings["expected"]),
        "false_scanner_findings": _rate(findings["scanner_false"], findings["scanner"]),
        "missed_explainer_findings": _rate(findings["explainer_missed"], findings["expected_in_report"]),
        "spurious_explainer_findings": _rate(findings["explainer_spurious"], findings["explained"]),
        "reports_with_spurious_attempts": _rate(findings["reports_with_spurious_attempts"], findings["reports"]),
    }
