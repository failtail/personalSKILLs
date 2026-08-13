#!/usr/bin/env python3
"""验证 Usage Promotion Queue 的聚合、过滤、证据边界和稳定排序。"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_usage_promotion_queue import build_queue, markdown_report


ARTIFACT_SET_ID = "sha256:" + "a" * 64


def make_surface() -> dict:
    """构造含直接成员和继承成员的最小 descriptor Surface。"""

    return {
        "schema_version": 1,
        "sdk_binding": {"artifact_set_id": ARTIFACT_SET_ID},
        "constructors": [{"owner": "THING.Box"}],
        "namespace_members": [
            {"owner": "THING.LoopType", "member": "Repeat", "kind": "property"}
        ],
        "prototype_members": [
            {
                "effective_owner": "THING.BaseObject",
                "declared_owner": "THING.BaseObject",
                "member": "destroy",
                "kind": "method",
            }
        ],
        "inheritance": [{"child": "THING.Entity", "parent": "THING.BaseObject"}],
    }


def entity(
    usage_id: str,
    canonical_key: str | None,
    path: str,
    line: int,
    *,
    production: bool = True,
    resolution: str = "resolved",
    access_type: str = "call",
) -> dict:
    """生成带稳定源码定位的测试 Usage Entity。"""

    return {
        "id": usage_id,
        "canonical_key": canonical_key,
        "access_type": access_type,
        "source": {"path": path, "line": line, "column": 2, "block": "module"},
        "resolution_status": resolution,
        "production_reachable": production,
    }


def main() -> int:
    """断言所有不变量，失败时返回非零供公共 Skill CI 使用。"""

    usage = {
        "usage_entities": [
            entity("u-destroy-1", "method|THING.Entity|destroy", "src/a.js", 10),
            entity("u-destroy-2", "method|THING.Entity|destroy", "src/b.js", 20),
            entity(
                "u-repeat",
                "property|THING.LoopType|Repeat",
                "src/a.js",
                30,
                access_type="read",
            ),
            entity("u-box", "constructor|THING.Box|constructor", "src/c.js", 40, access_type="construct"),
            entity("u-nonprod", "property|THING.Private|token", "src/dev.js", 50, production=False),
            entity("u-dynamic", None, "src/dynamic.js", 60, resolution="dynamic_unresolved"),
            entity("u-regex-like", "property|THING.NotInAst|member", "src/ref.js", 70, production=False),
        ],
        "discovery_findings": [{"token": "THING.RegexOnly", "classification": "discovery_only"}],
    }
    contract = {
        "contract_id": "thingjs-2.0.13-fixture",
        "sdk_binding": {"sdk_version": "2.0.13", "artifact_set_id": ARTIFACT_SET_ID},
        "apis": [],
    }
    registry = {
        "apis": [
            {
                "id": "fixture.destroy",
                "kind": "method",
                "owner": "THING.Entity",
                "name": "destroy",
                "evidence_labels": ["official_verified"],
                "sources": [
                    {
                        "ref": "official-entity",
                        "source_type": "official_api",
                        "url": "https://example.invalid/entity",
                        "version_relation": "unversioned_latest",
                    }
                ],
                "lifecycle": ["清理并清空拥有者引用"],
            }
        ]
    }

    queue = build_queue(usage, contract, make_surface(), registry)
    assert queue["summary"]["candidate_count"] == 3
    assert queue["summary"]["regex_discovery_count"] == 1
    assert queue["summary"]["excluded"]["non_production"] == 2
    assert queue["summary"]["excluded"]["unresolved"] == 1

    by_key = {item["canonical_key"]: item for item in queue["items"]}
    destroy = by_key["method|THING.Entity|destroy"]
    assert destroy["production_usage_count"] == 2
    assert destroy["production_file_count"] == 2
    assert destroy["runtime_evidence"]["status"] == "present"
    assert destroy["runtime_evidence"]["match"] == "inherited"
    assert destroy["official_evidence"]["status"] == "candidate"
    assert destroy["lifecycle_risk"]["requires_behavior_test"] is True

    repeat = by_key["property|THING.LoopType|Repeat"]
    assert repeat["runtime_evidence"]["status"] == "present"
    assert repeat["official_evidence"]["status"] == "missing"
    assert repeat["next_action"] == "补充受控官方 owner/signature 证据"

    markdown = markdown_report(queue)
    assert "Regex finding、非生产 token" in markdown
    assert "method|THING.Entity|destroy" in markdown
    assert "u-destroy-1" in markdown

    with tempfile.TemporaryDirectory(prefix="thingjs-promotion-test-") as directory:
        output = Path(directory) / "queue.json"
        output.write_text(json.dumps(queue, ensure_ascii=False), encoding="utf-8")
        assert json.loads(output.read_text(encoding="utf-8"))["schema_version"] == 1

    print(json.dumps({"valid": True, "candidate_count": len(queue["items"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
