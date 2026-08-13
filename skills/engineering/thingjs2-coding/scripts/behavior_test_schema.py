#!/usr/bin/env python3
"""Validate independent ThingJS lifecycle Behavior Test evidence.

The schema describes observations and machine-checkable invariants; it does not
promote an API into the Contract or claim that a synthetic scheduler is the
ThingJS runtime.
"""

from __future__ import annotations

import re
from typing import Any


SCHEMA_VERSION = 1
ARTIFACT_SET_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
CATEGORIES = {"app_load", "entity_readiness", "scene_replacement", "app_teardown"}
RESULT_STATUSES = {"passed", "failed", "conflict", "inconclusive", "not_tested"}
ASSERTION_STATUSES = {"passed", "failed", "not_evaluated"}
TRACE_EVENTS = {
    "operation.started",
    "operation.cancel_requested",
    "operation.settled",
    "resource.created",
    "resource.released",
    "listener.bound",
    "listener.unbound",
    "effect.applied",
    "teardown.requested",
    "teardown.completed",
}


def _issue(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def _required_string(value: Any, path: str, errors: list[dict[str, str]]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(_issue("required_string", path, "Expected a non-empty string."))


def _sequence(value: Any, path: str, errors: list[dict[str, str]]) -> None:
    if not isinstance(value, int) or value < 1:
        errors.append(_issue("sequence_invalid", path, "Expected a positive integer sequence."))


def _ledger(
    values: Any,
    path: str,
    *,
    released_field: str,
    errors: list[dict[str, str]],
) -> None:
    if not isinstance(values, list):
        errors.append(_issue("ledger_invalid", path, "Expected a resource/listener ledger array."))
        return
    seen: set[str] = set()
    for index, item in enumerate(values):
        item_path = f"{path}[{index}]"
        if not isinstance(item, dict):
            errors.append(_issue("ledger_item_invalid", item_path, "Ledger item must be an object."))
            continue
        item_id = item.get("id")
        _required_string(item_id, f"{item_path}.id", errors)
        if isinstance(item_id, str) and item_id in seen:
            errors.append(_issue("ledger_duplicate_id", f"{item_path}.id", "Ledger IDs must be unique."))
        if isinstance(item_id, str):
            seen.add(item_id)
        _required_string(item.get("owner_id"), f"{item_path}.owner_id", errors)
        _sequence(item.get("created_seq", item.get("bound_seq")), f"{item_path}.created_seq", errors)
        released_seq = item.get(released_field, item.get("released_seq", item.get("unbound_seq")))
        if released_seq is not None:
            _sequence(released_seq, f"{item_path}.{released_field}", errors)
            created_seq = item.get("created_seq", item.get("bound_seq"))
            if isinstance(created_seq, int) and isinstance(released_seq, int) and released_seq < created_seq:
                errors.append(_issue("cleanup_order", item_path, "Release/unbind must follow create/bind."))


def validate_behavior_test(test: Any) -> dict[str, Any]:
    """Validate schema shape and lifecycle invariants without executing ThingJS."""

    errors: list[dict[str, str]] = []
    if not isinstance(test, dict):
        return {"valid": False, "errors": [_issue("root_invalid", "$", "Behavior Test root must be an object.")]}
    if test.get("schema_version") != SCHEMA_VERSION:
        errors.append(_issue("schema_version", "schema_version", f"Expected schema version {SCHEMA_VERSION}."))
    _required_string(test.get("test_id"), "test_id", errors)
    if test.get("category") not in CATEGORIES:
        errors.append(_issue("category_invalid", "category", "Behavior Test category is not supported."))
    _required_string(test.get("scenario"), "scenario", errors)
    artifact_set_id = test.get("artifact_set_id")
    if not isinstance(artifact_set_id, str) or not ARTIFACT_SET_PATTERN.fullmatch(artifact_set_id):
        errors.append(_issue("artifact_set_invalid", "artifact_set_id", "Expected an exact sha256 Artifact Set identity."))
    contract_refs = test.get("contract_refs")
    if not isinstance(contract_refs, list) or not contract_refs or not all(isinstance(item, str) and item for item in contract_refs):
        errors.append(_issue("contract_refs_invalid", "contract_refs", "At least one canonical Contract reference is required."))
    if not isinstance(test.get("preconditions"), dict):
        errors.append(_issue("preconditions_invalid", "preconditions", "Preconditions must be an object."))
    if not isinstance(test.get("stimulus"), list):
        errors.append(_issue("stimulus_invalid", "stimulus", "Stimulus must be an event/action array."))

    trace = test.get("trace")
    if not isinstance(trace, list) or not trace:
        errors.append(_issue("trace_invalid", "trace", "Trace must contain ordered lifecycle events."))
        trace = []
    trace_sequences: set[int] = set()
    cancelled_operations: set[str] = set()
    for index, event in enumerate(trace):
        event_path = f"trace[{index}]"
        if not isinstance(event, dict):
            errors.append(_issue("trace_event_invalid", event_path, "Trace event must be an object."))
            continue
        sequence = event.get("seq")
        _sequence(sequence, f"{event_path}.seq", errors)
        if isinstance(sequence, int) and sequence in trace_sequences:
            errors.append(_issue("trace_sequence_duplicate", f"{event_path}.seq", "Trace sequence values must be unique."))
        if isinstance(sequence, int):
            trace_sequences.add(sequence)
        if event.get("event") not in TRACE_EVENTS:
            errors.append(_issue("trace_event_unknown", f"{event_path}.event", "Trace event is not supported."))
        if event.get("event") == "operation.cancel_requested":
            _required_string(event.get("op_id"), f"{event_path}.op_id", errors)
            if isinstance(event.get("op_id"), str):
                cancelled_operations.add(event["op_id"])
        if event.get("event") in {"operation.started", "operation.settled"}:
            _required_string(event.get("op_id"), f"{event_path}.op_id", errors)

    _ledger(test.get("resources"), "resources", released_field="released_seq", errors=errors)
    _ledger(test.get("listeners"), "listeners", released_field="unbound_seq", errors=errors)
    effects = test.get("effects")
    if not isinstance(effects, list):
        errors.append(_issue("effects_invalid", "effects", "Effects must be an array."))
        effects = []
    for index, effect in enumerate(effects):
        effect_path = f"effects[{index}]"
        if not isinstance(effect, dict):
            errors.append(_issue("effect_invalid", effect_path, "Effect must be an object."))
            continue
        _required_string(effect.get("id"), f"{effect_path}.id", errors)
        _required_string(effect.get("op_id"), f"{effect_path}.op_id", errors)
        _required_string(effect.get("owner_id"), f"{effect_path}.owner_id", errors)
        _sequence(effect.get("seq"), f"{effect_path}.seq", errors)
        if effect.get("op_id") in cancelled_operations and effect.get("accepted") is True:
            errors.append(_issue("late_effect_accepted", effect_path, "Cancelled operation cannot apply an accepted effect."))

    cleanup = test.get("cleanup")
    if not isinstance(cleanup, dict):
        errors.append(_issue("cleanup_invalid", "cleanup", "Cleanup must be an object."))
        cleanup = {}
    for field in ("requested_seq", "completed_seq"):
        _sequence(cleanup.get(field), f"cleanup.{field}", errors)
    if isinstance(cleanup.get("requested_seq"), int) and isinstance(cleanup.get("completed_seq"), int):
        if cleanup["completed_seq"] < cleanup["requested_seq"]:
            errors.append(_issue("cleanup_order", "cleanup", "Cleanup completion must follow its request."))
    for field in ("remaining_resources", "remaining_listeners", "late_effects"):
        if not isinstance(cleanup.get(field), list):
            errors.append(_issue("cleanup_residuals_invalid", f"cleanup.{field}", "Cleanup residuals must be arrays."))
    if not isinstance(cleanup.get("idempotent"), bool):
        errors.append(_issue("cleanup_idempotence_missing", "cleanup.idempotent", "Cleanup must state idempotence."))

    assertions = test.get("assertions")
    if not isinstance(assertions, list) or not assertions:
        errors.append(_issue("assertions_invalid", "assertions", "At least one machine assertion is required."))
        assertions = []
    else:
        for index, assertion in enumerate(assertions):
            assertion_path = f"assertions[{index}]"
            if not isinstance(assertion, dict):
                errors.append(_issue("assertion_invalid", assertion_path, "Assertion must be an object."))
                continue
            _required_string(assertion.get("id"), f"{assertion_path}.id", errors)
            if assertion.get("status") not in ASSERTION_STATUSES:
                errors.append(_issue("assertion_status_invalid", f"{assertion_path}.status", "Assertion status is not supported."))

    result = test.get("result")
    if not isinstance(result, dict):
        errors.append(_issue("result_invalid", "result", "Result must be an object."))
        result = {}
    status = result.get("status")
    if status not in RESULT_STATUSES:
        errors.append(_issue("result_status_invalid", "result.status", "Result status is not supported."))
    _required_string(result.get("evidence_ref"), "result.evidence_ref", errors)
    if status == "passed":
        if any(assertion.get("status") != "passed" for assertion in assertions if isinstance(assertion, dict)):
            errors.append(_issue("passed_assertion_failed", "assertions", "Passed result requires every assertion to pass."))
        if cleanup.get("remaining_resources") or cleanup.get("remaining_listeners") or cleanup.get("late_effects"):
            errors.append(_issue("passed_cleanup_residual", "cleanup", "Passed result cannot retain cleanup residuals."))
        if cleanup.get("idempotent") is not True:
            errors.append(_issue("passed_cleanup_not_idempotent", "cleanup.idempotent", "Passed result requires idempotent cleanup."))

    return {"valid": not errors, "errors": errors}
