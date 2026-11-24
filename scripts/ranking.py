"""Apply the tier policy to explicit reviewer judgements and dated source evidence."""

from datetime import timedelta

from run_validation import iso_date

SCREENER_GROUP = {
    "founder": 0, "hiring_manager": 0, "talent_team": 1,
    "agency": 2, "recruiter": 2, "unknown": 2,
}
PROSPECT = {"stronger": 0, "plausible": 1, "stretch": 2}
CONFIDENCE = {"high": 0, "medium": 1, "low": 2}
PREFERENCE = {"wanted": 0, "acceptable": 1, "unwanted": 2}
ELIGIBILITY = ("eligible", "conditional", "ineligible")
REQUIREMENT_TYPES = ("hard", "nice", "duty")
REQUIREMENT_FIT = ("met", "partial", "not_met", "not_assessed")
VISIBILITY = ("cv", "portfolio", "none")


def _has_text(value):
    return isinstance(value, str) and bool(value.strip())


def _require(value, choices, field):
    if value not in tuple(choices):
        raise ValueError(f"{field} must be one of: {', '.join(choices)}")


def recency(evidence, run_date, max_days):
    """Prefer the earliest established first-party date across equivalent listings."""
    today = iso_date(run_date)
    cutoff = today - timedelta(days=max_days)
    first_party = [item for item in evidence if item["source_kind"] == "first_party"]
    original = [iso_date(item["date"]) for item in first_party if item["kind"] == "original_publication"]
    published = [iso_date(item["date"]) for item in first_party if item["kind"] in
                 ("publication", "original_publication")]
    seen = [iso_date(item["date"]) for item in first_party if item["kind"] == "observed"]
    earliest = min(published + seen, default=None)
    certainty = "unknown"
    if original and min(original) == earliest:
        certainty = "confirmed"
    elif published or (earliest is not None and earliest < cutoff):
        certainty = "inferred"

    if earliest and earliest < cutoff:
        verdict = "stale"
    elif published:
        verdict = "recent"
    else:
        verdict = "unknown"
    return {
        "verdict": verdict,
        "original_posted_status": certainty,
        "earliest_first_party_date": earliest.isoformat() if earliest else None,
        "earliest_publication": min(published).isoformat() if published else None,
    }


def _validate_review(review, status):
    _require(review.get("review_method"), ("human", "model_reviewer"), "review_method")
    _require(review.get("practical_eligibility"), ELIGIBILITY, "practical_eligibility")
    _require(review.get("preference_fit"), PREFERENCE, "preference_fit")
    _require(review.get("interview_prospect"), PROSPECT, "interview_prospect")
    _require(review.get("confidence"), CONFIDENCE, "confidence")
    _require(review.get("screener"), SCREENER_GROUP, "screener")
    for field in ("central_work", "fit_reason", "practical_notes"):
        if not _has_text(review.get(field)):
            raise ValueError(f"assessed records require {field}")
    if review["screener"] != "unknown" and not _has_text(review.get("screener_evidence")):
        raise ValueError("a known screener requires screener_evidence")
    if status == "assessed-provisional" and review.get("review_source") == "first_party":
        raise ValueError("provisional assessment cannot claim a first-party review")
    requirements = review.get("requirements")
    if not isinstance(requirements, list):
        raise ValueError("requirements must be a list, empty if the posting has none")
    for item in requirements:
        if not isinstance(item, dict) or not _has_text(item.get("text")):
            raise ValueError("each requirement must include the relevant posting text")
        _require(item.get("kind"), REQUIREMENT_TYPES, "requirement kind")
        _require(item.get("fit"), REQUIREMENT_FIT, "requirement fit")
        _require(item.get("visibility"), VISIBILITY, "requirement visibility")
        if item["fit"] in ("met", "partial") and not _has_text(item.get("evidence")):
            raise ValueError("met or partial requirements require candidate evidence")
        if item["kind"] == "hard" and item["fit"] == "met" and item["visibility"] != "cv":
            raise ValueError("a HARD requirement is met only when supported by the CV")
    return [item for item in requirements if item["kind"] == "hard"]


def assess(candidate, review, *, run_date, max_days, tracked=None):
    date_signal = recency(candidate["date_evidence"], run_date, max_days)
    status = review.get("review_status", "pending")
    _require(status, ("assessed", "assessed-provisional", "pending", "incomplete"), "review_status")
    source = candidate["source_kind"]
    record = {
        key: candidate[key] for key in
        ("seat_key", "company", "exact_title", "url", "location", "checked_at", "date_evidence", "source_urls")
    }
    if candidate.get("identity_evidence"):
        record["identity_evidence"] = candidate["identity_evidence"]
    record.update(
        review_status=status, active_status="live" if candidate["active"] else "unconfirmed",
        source_kind=source, recency=date_signal, disposition=status,
    )
    if status in ("pending", "incomplete"):
        return record

    if status == "assessed" and (source != "first_party" or not candidate["description"]):
        raise ValueError("an assessed record needs a captured first-party description")
    hard = _validate_review(review, status)
    record.update({
        key: review[key] for key in (
            "review_method", "practical_eligibility", "preference_fit", "interview_prospect",
            "confidence", "screener", "central_work", "fit_reason", "practical_notes", "requirements",
        )
    })
    for key in ("screener_evidence", "change_reason", "previous_disposition",
                "optional_reason", "override_reason", "recommended_effort", "application_surface"):
        if _has_text(review.get(key)):
            record[key] = review[key].strip()

    contested = sum(item["fit"] in ("partial", "not_assessed") for item in hard)
    hard_gap = any(item["fit"] == "not_met" for item in hard)
    if hard_gap:
        record["interview_prospect"] = "stretch"
    if contested >= 2:
        record["confidence"] = "low"
    record["contested_hard_lines"] = contested

    hiring = review.get("fresh_hiring_evidence")
    fresh_hiring = False
    if isinstance(hiring, dict) and _has_text(hiring.get("note")):
        from run_validation import web_url

        if not web_url(hiring.get("url")):
            raise ValueError("fresh hiring evidence requires its source URL")
        checked = iso_date(hiring.get("date"))
        fresh_hiring = 0 <= (iso_date(run_date) - checked).days <= 14
        record["fresh_hiring_evidence"] = hiring

    if tracked in ("submitted", "interviewing", "dismissed"):
        reason, disposition = f"Already tracked as {tracked}.", "skip"
    elif record["practical_eligibility"] == "ineligible":
        reason, disposition = "Practical requirements are not met.", "skip"
    elif record["preference_fit"] == "unwanted":
        reason, disposition = "Daily work is outside the search preferences.", "skip"
    elif not candidate["active"]:
        reason, disposition = "Current liveness is unconfirmed.", "skip"
    elif date_signal["verdict"] == "stale" and not (fresh_hiring or record.get("override_reason")):
        reason, disposition = "Past the recency window with no fresh hiring evidence.", "skip"
    elif record["interview_prospect"] == "stretch" and not record.get("override_reason"):
        reason, disposition = "Stretch on the documented requirements or central work.", "skip"
    elif record.get("optional_reason"):
        reason, disposition = "Optional follow-up at the candidate's discretion.", "apply_if_time"
    elif (status == "assessed" and record["practical_eligibility"] == "eligible"
          and record["preference_fit"] == "wanted" and record["interview_prospect"] != "stretch"
          and not contested and date_signal["verdict"] == "recent"):
        reason, disposition = "Live employer listing with eligible, evidenced fit.", "apply_now"
    else:
        reason, disposition = "Review the documented conditions before applying.", "apply_if_time"
    record.update(disposition=disposition, disposition_reason=reason)
    return record


def rank_key(record):
    date = record["recency"]["earliest_first_party_date"]
    return (
        record["disposition"] != "apply_now",
        SCREENER_GROUP[record["screener"]],
        PROSPECT[record["interview_prospect"]],
        record["contested_hard_lines"] >= 2,
        CONFIDENCE[record["confidence"]],
        PREFERENCE[record["preference_fit"]],
        record["source_kind"] != "first_party",
        -iso_date(date).toordinal() if date else 0,
        record["company"].casefold(), record["exact_title"].casefold(), record["seat_key"],
    )
