#!/usr/bin/env python3
"""对 AST Usage 与 Contract 门禁执行不依赖真实 ThingJS 制品的合成回归。"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from build_versioned_contract import normalize_record
from validate_contract import validate_all


FIXTURE_SHA256 = "a" * 64
FIXTURE_IDENTITY = f"core|thing.min.js|{FIXTURE_SHA256}"
FIXTURE_ARTIFACT_SET_ID = f"sha256:{hashlib.sha256(FIXTURE_IDENTITY.encode('utf-8')).hexdigest()}"


def parse_args() -> argparse.Namespace:
    """测试 AST 时需要一个已安装 Babel/Vue parser 的 Node 项目。"""

    parser = argparse.ArgumentParser(description="Smoke-test the ThingJS Contract pipeline.")
    parser.add_argument("--parser-root", required=True)
    parser.add_argument("--node", default="node")
    return parser.parse_args()


def make_binding(sha256: str = FIXTURE_SHA256) -> dict:
    """构造最小 Artifact Set；哈希变化测试使用相同结构。"""

    return {
        "sdk_version": "2.0.13",
        "artifact_set_id": (
            FIXTURE_ARTIFACT_SET_ID
            if sha256 == FIXTURE_SHA256
            else f"sha256:{hashlib.sha256(f'core|thing.min.js|{sha256}'.encode('utf-8')).hexdigest()}"
        ),
        "artifacts": [
            {
                "role": "core",
                "path": "thing.min.js",
                "sha256": sha256,
            }
        ],
    }


def make_record(kind: str, owner: str, name: str, source_relation: str = "exact") -> dict:
    """构造具受控官方证据和 Runtime 存在性状态的 Contract 记录。"""

    return {
        "id": f"fixture.{owner}.{name}",
        "kind": kind,
        "owner": owner,
        "name": name,
        "contract_state": "existence_verified",
        "usage_state": "allowed",
        "sources": [
            {
                "source_type": "official_api",
                "url": "https://example.invalid/official",
                "version_relation": source_relation,
                "content_sha256": "c" * 64 if source_relation != "unversioned_latest" else None,
            }
        ],
        "signatures": [{"text": f"{owner}.{name}", "source_refs": ["fixture"]}],
        "existence_evidence": {
            "status": "supported",
            "artifact_set_id": FIXTURE_ARTIFACT_SET_ID,
        },
    }


def make_contract() -> dict:
    """覆盖直接构造、直接方法和继承方法三类匹配。"""

    return {
        "schema_version": 2,
        "sdk_binding": make_binding(),
        "apis": [
            make_record("constructor", "THING.App", "constructor", "unversioned_latest"),
            make_record("constructor", "THING.Entity", "constructor"),
            make_record("method", "THING.App", "on"),
            make_record("method", "THING.BaseObject", "destroy"),
        ],
    }


def make_surface() -> dict:
    """Surface 只证明成员存在，并通过 inheritance 连接 Entity/BaseObject。"""

    return {
        "schema_version": 1,
        "sdk_binding": make_binding(),
        "runtime_version": "2.0.13",
        "constructors": [
            {"owner": "THING.App"},
            {"owner": "THING.Entity"},
            {"owner": "THING.BaseObject"},
        ],
        "namespace_members": [],
        "prototype_members": [
            {
                "effective_owner": "THING.App",
                "declared_owner": "THING.App",
                "member": "on",
                "kind": "method",
            },
            {
                "effective_owner": "THING.BaseObject",
                "declared_owner": "THING.BaseObject",
                "member": "destroy",
                "kind": "method",
            },
        ],
        "inheritance": [{"child": "THING.Entity", "parent": "THING.BaseObject"}],
        "capture": {"mode": "browser_descriptor_probe", "page_errors": []},
    }


def run_usage_extractor(node: str, parser_root: str, temp_root: Path) -> dict:
    """验证 alias、destructuring、静态 computed property、Vue SFC 和动态阻断。"""

    (temp_root / "src").mkdir()
    (temp_root / "index.html").write_text(
        '<script type="module" src="/src/main.js"></script>\n',
        encoding="utf-8",
    )
    (temp_root / "src" / "main.js").write_text(
        "\n".join(
            [
                "import './View.vue'",
                "import '@/helper'",
                "import './missing-local.js'",
                "const T = THING",
                "const { Entity } = T",
                "const appClass = 'App'",
                "const app = new T[appClass]()",
                "const entity = new Entity()",
                "const { destroy: destroyEntity } = entity",
                "app.on('click', null, () => {}, 'fixture')",
                "entity.destroy()",
                "destroyEntity()",
                "new THING[window.runtimeClass]()",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (temp_root / "src" / "View.vue").write_text(
        "<script setup lang=\"ts\">\nconst app = new THING.App()\n</script>\n",
        encoding="utf-8",
    )
    (temp_root / "src" / "helper.ts").write_text(
        "export const helperEntity = new THING.Entity()\n",
        encoding="utf-8",
    )
    (temp_root / "src" / "broken.js").write_text(
        "const broken = THING.ParseFallback(\n",
        encoding="utf-8",
    )
    (temp_root / ".codex-ref").mkdir()
    (temp_root / ".codex-ref" / "reference.js").write_text(
        "new THING.ReferenceOnly()\n",
        encoding="utf-8",
    )
    output = temp_root / "usage.json"
    extractor = Path(__file__).resolve().parent / "extract_usage_surface.mjs"
    subprocess.run(
        [
            node,
            str(extractor),
            "--project-root",
            str(temp_root),
            "--parser-root",
            parser_root,
            "--output",
            str(output),
            "--entry",
            "src/main.js",
            "--entry",
            "src/broken.js",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(output.read_text(encoding="utf-8"))


def run_runtime_probe_safety(node: str, temp_root: Path) -> dict:
    """用会抛错的 getter 证明 probe 只读取 descriptor.value。"""

    probe = Path(__file__).resolve().parent / "runtime_surface_probe.js"
    fixture = temp_root / "probe-safety.cjs"
    fixture.write_text(
        "\n".join(
            [
                "globalThis.THING = {}",
                "Object.defineProperty(globalThis.THING, 'VERSION', { get() { throw new Error('VERSION getter invoked') } })",
                "Object.defineProperty(globalThis.THING, 'Danger', { get() { throw new Error('Danger getter invoked') } })",
                "globalThis.THING.App = function App() {}",
                f"const collect = require({json.dumps(str(probe))})",
                "process.stdout.write(JSON.stringify(collect()))",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    completed = subprocess.run(
        [node, str(fixture)],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def main() -> int:
    """断言核心不变量；任何失败直接使公共 Skill CI 非零退出。"""

    args = parse_args()
    with tempfile.TemporaryDirectory(prefix="thingjs-contract-test-") as directory:
        temp_root = Path(directory)
        usage = run_usage_extractor(args.node, args.parser_root, temp_root)
        safe_surface = run_runtime_probe_safety(args.node, temp_root)

    assert safe_surface["runtime_version"] is None
    assert any(item["owner"] == "THING.App" for item in safe_surface["constructors"])

    entities = usage["usage_entities"]
    keys = {entity["canonical_key"] for entity in entities if entity["canonical_key"]}
    assert "constructor|THING.App|constructor" in keys
    assert "constructor|THING.Entity|constructor" in keys
    assert "method|THING.App|on" in keys
    assert "method|THING.Entity|destroy" in keys
    dynamic = [entity for entity in entities if entity["resolution_status"] == "dynamic_unresolved"]
    assert len(dynamic) == 1 and dynamic[0]["production_reachable"] is True
    assert any("destructure:Entity->Entity" in entity["alias_provenance"] for entity in entities)
    assert any(
        entity["canonical_key"] == "method|THING.Entity|destroy"
        and "destructure:destroy->destroyEntity" in entity["alias_provenance"]
        for entity in entities
    )
    assert any(
        entity["source"]["path"] == "src/helper.ts" and entity["production_reachable"] is True
        for entity in entities
    )
    assert any(
        gap["reason"] == "local_import_unresolved" and gap["production_reachable"] is True
        for gap in usage["reachability_gaps"]
    )
    assert len(usage["parse_failures"]) == 1
    assert usage["parse_failures"][0]["path"] == "src/broken.js"
    assert any(
        finding["classification"] == "discovery_only"
        and finding["reason"] == "parse_failure"
        for finding in usage["discovery_findings"]
    )
    assert not any(
        entity.get("canonical_key") == "constructor|THING.ReferenceOnly|constructor"
        for entity in entities
    )

    contract = make_contract()
    surface = make_surface()
    report = validate_all(contract, surface, usage, None)
    assert report["valid"] is False
    assert any(error["code"] == "dynamic_usage_blocked" for error in report["errors"])
    assert any(error["code"] == "production_parse_failure" for error in report["errors"])
    assert any(error["code"] == "production_reachability_gap" for error in report["errors"])
    assert any(warning["code"] == "stale_review" for warning in report["warnings"])
    assert not any(error["code"] == "usage_not_in_contract" and error.get("canonical_key") == "method|THING.Entity|destroy" for error in report["errors"])

    allowlist = {
        "entries": [
            {
                "status": "active",
                "artifact_set_id": FIXTURE_ARTIFACT_SET_ID,
                "usage_ids": [dynamic[0]["id"]],
                "dynamic_pattern": dynamic[0]["expression"],
                "reason": "Synthetic test exception.",
                "evidence_refs": ["fixture-evidence"],
            }
        ]
    }
    allowlisted_report = validate_all(contract, surface, usage, allowlist)
    assert not any(error["code"] == "dynamic_usage_blocked" for error in allowlisted_report["errors"])

    broad_allowlist = {
        "entries": [
            {
                "status": "active",
                "artifact_set_id": FIXTURE_ARTIFACT_SET_ID,
                "usage_ids": [],
                "dynamic_pattern": "*",
                "reason": "Synthetic broad exception.",
                "evidence_refs": ["fixture-evidence"],
            }
        ]
    }
    broad_report = validate_all(contract, surface, usage, broad_allowlist)
    assert any(error["code"] == "dynamic_usage_blocked" for error in broad_report["errors"])

    drift_profile = {
        "sdk_artifacts": [
            {
                "path": "thing.min.js",
                "sha256": "b" * 64,
            }
        ]
    }
    drift_report = validate_all(contract, surface, None, None, drift_profile)
    assert any(error["code"] == "project_artifact_drift" for error in drift_report["errors"])

    invalid_identity_surface = json.loads(json.dumps(surface))
    invalid_identity_surface["sdk_binding"]["artifact_set_id"] = "sha256:" + "0" * 64
    invalid_identity_report = validate_all(contract, invalid_identity_surface, None, None)
    assert any(error["code"] == "artifact_set_identity" for error in invalid_identity_report["errors"])

    browser_error_surface = json.loads(json.dumps(surface))
    browser_error_surface["capture"]["page_errors"] = ["fixture load error"]
    browser_error_report = validate_all(contract, browser_error_surface, None, None)
    assert any(error["code"] == "runtime_capture_errors" for error in browser_error_report["errors"])

    legacy_record = make_record("method", "THING.App", "on")
    legacy_record["runtime_verifications"] = [{"status": "supported"}]
    normalized_legacy = normalize_record(
        legacy_record,
        "2.0.13",
        FIXTURE_ARTIFACT_SET_ID,
        surface,
    )
    assert normalized_legacy["contract_state"] == "existence_verified"
    assert normalized_legacy["behavior_evidence"] == []

    wrong_kind_record = make_record("property", "THING.App", "on")
    normalized_wrong_kind = normalize_record(
        wrong_kind_record,
        "2.0.13",
        FIXTURE_ARTIFACT_SET_ID,
        surface,
    )
    assert normalized_wrong_kind["contract_state"] == "documented"

    exact_conflict_record = make_record("method", "THING.App", "on")
    exact_conflict_record["evidence_conflicts"] = [
        {"status": "mismatch", "version_relation": "exact", "evidence_ref": "fixture-exact"}
    ]
    normalized_exact_conflict = normalize_record(
        exact_conflict_record,
        "2.0.13",
        FIXTURE_ARTIFACT_SET_ID,
        surface,
    )
    assert normalized_exact_conflict["contract_state"] == "blocked"

    latest_conflict_record = make_record("method", "THING.App", "on")
    latest_conflict_record["evidence_conflicts"] = [
        {
            "status": "mismatch",
            "version_relation": "unversioned_latest",
            "evidence_ref": "fixture-latest",
        }
    ]
    normalized_latest_conflict = normalize_record(
        latest_conflict_record,
        "2.0.13",
        FIXTURE_ARTIFACT_SET_ID,
        surface,
    )
    assert normalized_latest_conflict["contract_state"] == "existence_verified"

    print(
        json.dumps(
            {
                "valid": True,
                "usage_entities": len(entities),
                "dynamic_unresolved": len(dynamic),
                "checks": [
                    "ast_alias_destructuring_computed",
                    "destructured_instance_method_alias",
                    "vue_script_setup",
                    "root_alias_reachability",
                    "unresolved_production_import_block",
                    "dynamic_ci_block",
                    "artifact_bound_allowlist",
                    "broad_allowlist_rejected",
                    "inherited_owner_resolution",
                    "unversioned_latest_stale_review",
                    "project_artifact_drift",
                    "artifact_set_identity_recomputed",
                    "browser_capture_error_blocks",
                    "regex_discovery_fallback_only",
                    "legacy_runtime_does_not_promote_behavior",
                    "generated_reference_directory_exclusion",
                    "controlled_mismatch_blocks_latest_only_reviews",
                    "runtime_probe_does_not_invoke_getters",
                    "runtime_member_kind_must_match",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
