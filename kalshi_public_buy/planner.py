"""Deterministic synthetic-data planner. No transport or credential surface."""
import hashlib
import json
import re

BUILD = "KALBUY-PUBLIC-69.99.1-EVIDENCE-REVIEW"
SCHEMA = "kalshi-public-snapshot-v2"
TEXT_FIELDS = {"market", "round", "scope", "observed_scope", "route", "observed_route"}
BOOL_FIELDS = {"synthetic", "market_open", "exchange_ready", "evidence_complete", "fees_complete", "prior_intent_ambiguous"}
COMMON_FIELDS = TEXT_FIELDS | BOOL_FIELDS | {"schema", "side", "status_build", "age_seconds", "status_age_seconds", "fee_age_seconds", "seen_intent_ids"}
INTEGER_FIELDS = ['balance_cents', 'entry_fee_cents', 'position_contracts', 'open_contracts', 'best_ask_cents']
EXTRA_BOOLS = ['one_cent_supported']
REQUIRED = COMMON_FIELDS | set(INTEGER_FIELDS) | set(EXTRA_BOOLS)


def outcome(status, reason, **details):
    return {"status": status, "reason": reason, "mode": "OFFLINE_ONLY", "synthetic": True, **details}


def plan(snapshot):
    """Fail closed; input quantities and fees are invented evidence, never live data."""
    if not isinstance(snapshot, dict) or set(snapshot) not in (REQUIRED, REQUIRED | {"analysis_evidence"}):
        return outcome("INVALID", "SCHEMA_MISMATCH")
    s = snapshot
    analysis = None
    if "analysis_evidence" in s:
        analysis = review_evidence(s["analysis_evidence"])
        if analysis["status"] == "INVALID":
            return outcome("INVALID", "INVALID_ANALYSIS_EVIDENCE")
    if s["schema"] != SCHEMA or s["synthetic"] is not True or s["side"] not in ("yes", "no"):
        return outcome("INVALID", "SYNTHETIC_INPUT_REQUIRED")
    for key in TEXT_FIELDS:
        if not isinstance(s[key], str) or not re.fullmatch(r"SYNTHETIC-[A-Z0-9_-]{1,40}", s[key]):
            return outcome("INVALID", "SYNTHETIC_IDENTIFIER_REQUIRED")
    if any(type(s[key]) is not bool for key in BOOL_FIELDS | set(EXTRA_BOOLS)):
        return outcome("INVALID", "BOOLEAN_REQUIRED")
    for key in ("age_seconds", "status_age_seconds", "fee_age_seconds", *INTEGER_FIELDS):
        if type(s[key]) is not int or not 0 <= s[key] <= 1000000:
            return outcome("INVALID", "BOUNDED_INTEGER_REQUIRED")
    seen = s["seen_intent_ids"]
    if not isinstance(seen, list) or len(seen) > 100 or any(not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value) for value in seen):
        return outcome("INVALID", "INVALID_INTENT_EVIDENCE")
    if s["status_build"] != BUILD:
        return outcome("QUARANTINE", "STATUS_IDENTITY_CONFLICT")
    if s["scope"] != s["observed_scope"] or s["route"] != s["observed_route"]:
        return outcome("QUARANTINE", "SCOPE_OR_ROUTE_CONFLICT")
    if s["prior_intent_ambiguous"]:
        return outcome("QUARANTINE", "RECONCILIATION_REQUIRED")
    if max(s["age_seconds"], s["status_age_seconds"], s["fee_age_seconds"]) > 30:
        return outcome("HOLD", "STALE_EVIDENCE")
    if not s["evidence_complete"] or not s["fees_complete"]:
        return outcome("HOLD", "INCOMPLETE_EVIDENCE")
    if not s["market_open"] or not s["exchange_ready"]:
        return outcome("HOLD", "UNAVAILABLE")
    quantity, price = 10, 1
    if not s["one_cent_supported"]:
        return outcome("HOLD", "UNSUPPORTED_PRICE_GRID")
    if not 1 <= s["best_ask_cents"] <= 99:
        return outcome("INVALID", "INVALID_BOOK_PRICE")
    if s["best_ask_cents"] <= price:
        return outcome("HOLD", "POST_ONLY_WOULD_CROSS")
    if s["position_contracts"] or s["open_contracts"]:
        return outcome("HOLD", "EXISTING_EXPOSURE")
    required_funding = quantity * price + s["entry_fee_cents"]
    if s["balance_cents"] < required_funding:
        return outcome("HOLD", "INSUFFICIENT_SCOPED_FUNDS")
    identity_extra = {}
    details = {"principal_cents": 10, "modeled_entry_fee_cents": s["entry_fee_cents"],
               "required_funding_cents": required_funding, "post_only": True}
    if analysis is not None:
        details["analysis_review"] = analysis
    identity = {key: s[key] for key in ("market", "round", "side", "scope", "route")}
    identity.update({"action": "buy", "quantity": quantity, "price_cents": price, **identity_extra})
    intent_id = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if intent_id in seen:
        return outcome("HOLD", "DUPLICATE_INTENT")
    return outcome("PLAN", "SYNTHETIC_PLAN_ONLY", intent_id=intent_id,
                   quantity=quantity, price_cents=price, **details)


def review_evidence(evidence):
    """Ordered, optional research checks; never promote a model or veto a plan."""
    flags = {"history_complete", "lifecycle_fee_complete", "chronological_holdout_complete"}
    numbers = {"age_seconds", "independent_response_count"}
    if not isinstance(evidence, dict) or set(evidence) != flags | numbers:
        return {"status": "INVALID", "reason": "SCHEMA_MISMATCH"}
    if any(type(evidence[key]) is not bool for key in flags):
        return {"status": "INVALID", "reason": "BOOLEAN_REQUIRED"}
    if any(type(evidence[key]) is not int or not 0 <= evidence[key] <= 1000000 for key in numbers):
        return {"status": "INVALID", "reason": "BOUNDED_INTEGER_REQUIRED"}
    if evidence["independent_response_count"] < 6:
        return {"status": "NEUTRAL", "reason": "INSUFFICIENT_INDEPENDENT_RESPONSES"}
    if not evidence["history_complete"]:
        return {"status": "BLOCKED", "reason": "INCOMPLETE_HISTORY"}
    if evidence["age_seconds"] > 30:
        return {"status": "BLOCKED", "reason": "STALE_ANALYSIS_EVIDENCE"}
    if not evidence["lifecycle_fee_complete"]:
        return {"status": "BLOCKED", "reason": "INCOMPLETE_LIFECYCLE_FEES"}
    if not evidence["chronological_holdout_complete"]:
        return {"status": "BLOCKED", "reason": "HOLDOUT_NOT_COMPLETE"}
    return {"status": "READY_FOR_REVIEW", "reason": "NO_AUTOMATIC_PROMOTION"}
