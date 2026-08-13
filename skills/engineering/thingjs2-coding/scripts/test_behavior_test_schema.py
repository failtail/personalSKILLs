#!/usr/bin/env python3
"""Synthetic regression for lifecycle trace and cleanup invariants."""

from __future__ import annotations

import copy
import json

from behavior_test_schema import validate_behavior_test


def fixture() -> dict:
    """Build a scene-replacement trace without invoking a ThingJS runtime."""

    return {
        "schema_version": 1,
        "test_id": "fixture.scene-replacement-late-completion",
        "category": "scene_replacement",
        "scenario": "cancelled generation settles after the replacement commits",
        "artifact_set_id": "sha256:" + "a" * 64,
        "contract_refs": ["thingjs2.api.THING.App.load"],
        "preconditions": {"app_id": "app-1", "current_generation": 2},
        "stimulus": [
            {"seq": 1, "action": "start_load", "op_id": "load-1", "generation": 1},
            {"seq": 2, "action": "replace_scene", "op_id": "load-2", "generation": 2},
        ],
        "trace": [
            {"seq": 1, "event": "operation.started", "op_id": "load-1", "owner_id": "app-1", "generation": 1},
            {"seq": 2, "event": "operation.cancel_requested", "op_id": "load-1", "owner_id": "app-1", "reason": "scene_replaced"},
            {"seq": 3, "event": "operation.started", "op_id": "load-2", "owner_id": "app-1", "generation": 2},
            {"seq": 4, "event": "operation.settled", "op_id": "load-2", "owner_id": "app-1", "settlement": "fulfilled", "accepted": True},
            {"seq": 5, "event": "operation.settled", "op_id": "load-1", "owner_id": "app-1", "settlement": "fulfilled", "accepted": False},
            {"seq": 6, "event": "teardown.requested", "owner_id": "app-1"},
            {"seq": 7, "event": "teardown.completed", "owner_id": "app-1"},
        ],
        "resources": [
            {"id": "scene-old", "kind": "scene", "owner_id": "app-1", "state": "destroyed", "created_seq": 1, "released_seq": 7},
            {"id": "scene-new", "kind": "scene", "owner_id": "app-1", "state": "active", "created_seq": 3},
        ],
        "listeners": [
            {"id": "listener-old", "owner_id": "scene-old", "target_id": "scene-old", "event": "update", "bound_seq": 1, "unbound_seq": 7},
        ],
        "effects": [
            {"id": "effect-new-scene", "op_id": "load-2", "owner_id": "app-1", "target_id": "scene-new", "kind": "scene_commit", "seq": 4, "accepted": True},
        ],
        "assertions": [
            {"id": "cancelled-late-settlement-rejected", "status": "passed"},
            {"id": "old-listener-unbound", "status": "passed"},
            {"id": "cleanup-idempotent", "status": "passed"},
        ],
        "cleanup": {
            "requested_seq": 6,
            "completed_seq": 7,
            "remaining_resources": [],
            "remaining_listeners": [],
            "late_effects": [],
            "idempotent": True,
        },
        "result": {"status": "passed", "evidence_ref": "behavior-tests/fixture-scene-replacement.json"},
    }


def main() -> int:
    valid = validate_behavior_test(fixture())
    assert valid["valid"], valid

    stale_effect = copy.deepcopy(fixture())
    stale_effect["effects"].append(
        {"id": "effect-stale", "op_id": "load-1", "owner_id": "app-1", "target_id": "scene-old", "kind": "scene_commit", "seq": 5, "accepted": True}
    )
    invalid = validate_behavior_test(stale_effect)
    assert not invalid["valid"]
    assert any(error["code"] == "late_effect_accepted" for error in invalid["errors"])

    print(json.dumps({"valid": True, "fixture_status": "passed", "negative_invariant": "late_effect_accepted"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
