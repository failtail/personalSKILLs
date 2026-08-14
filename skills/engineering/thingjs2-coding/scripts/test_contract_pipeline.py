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


def make_structured_resolver_contract() -> dict:
    """为 nested-instance resolver 提供受控 return owner，不从 runtime 推导类型。"""

    def record(kind: str, owner: str, name: str, return_type: dict) -> dict:
        return {
            "id": f"structured.{owner}.{name}",
            "kind": kind,
            "owner": owner,
            "name": name,
            "contract_state": "existence_verified",
            "usage_state": "allowed",
            "signatures": [
                {
                    "text": f"{owner}.{name}",
                    "parameters": [],
                    "return_type": return_type,
                    "async": False,
                    "lifecycle": [],
                }
            ],
        }

    return {
        "schema_version": 3,
        "signature_schema_version": 1,
        "contract_id": "fixture-resolver-v2",
        "apis": [
            record("property", "THING.Entity", "scene", {"kind": "reference", "name": "THING.Scene"}),
            record("method", "THING.Entity", "getScene", {"kind": "reference", "name": "THING.Scene"}),
            record("method", "THING.Scene", "load", {"kind": "primitive", "name": "boolean"}),
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
                "import '@custom/helper'",
                "import { ImportedEntity, ImportedEntityClass, ReExportedApp } from './consumer-exports.js'",
                "import * as ThingExports from './cross-module.js'",
                "import { ConflictingClass } from './conflicting-exports.js'",
                "import { makeEntity, makeArrowEntity } from './cross-module.js'",
                "import makeDefaultEntity from './default-factory.js'",
                "import { plainArrayHelper } from './plain-helper.js'",
                "import './missing-local.js'",
                "const T = THING",
                "const { Entity } = T",
                "const appClass = 'App'",
                "const app = new T[appClass]()",
                "const entity = new Entity()",
                "const scene = entity.scene",
                "scene.load()",
                "entity.getScene().load()",
                "const { destroy: destroyEntity } = entity",
                "app.on('click', null, () => {}, 'fixture')",
                "entity.destroy()",
                "destroyEntity()",
                "ImportedEntity.destroy()",
                "new ImportedEntityClass()",
                "new ReExportedApp()",
                "ThingExports.exportedEntity.destroy()",
                "new ConflictingClass()",
                "makeEntity().destroy()",
                "makeArrowEntity().destroy()",
                "makeDefaultEntity().destroy()",
                "plainArrayHelper().map((item) => item.id)",
                "const DynamicThingExports = await import('./cross-module.js')",
                "new DynamicThingExports.EntityClass()",
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
    (temp_root / "src" / "cross-module.js").write_text(
        "\n".join(
            [
                "export const exportedEntity = new THING.Entity()",
                "export const EntityClass = THING.Entity",
                "export function makeEntity() { return new THING.Entity() }",
                "export const makeArrowEntity = () => new THING.Entity()",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (temp_root / "src" / "consumer-exports.js").write_text(
        "export { exportedEntity as ImportedEntity, EntityClass as ImportedEntityClass } from './cross-module.js'\n"
        "export { makeArrowEntity } from './cross-module.js'\n"
        "export { default as ReExportedApp } from './default-app.js'\n",
        encoding="utf-8",
    )
    (temp_root / "src" / "default-app.js").write_text(
        "const AppClass = THING.App\nexport default AppClass\n",
        encoding="utf-8",
    )
    (temp_root / "src" / "default-factory.js").write_text(
        "export default () => new THING.Entity()\n",
        encoding="utf-8",
    )
    (temp_root / "src" / "plain-helper.js").write_text(
        "export function plainArrayHelper() { return [] }\n",
        encoding="utf-8",
    )
    (temp_root / "src" / "conflicting-exports.js").write_text(
        "export * from './conflict-entity.js'\nexport * from './conflict-app.js'\n",
        encoding="utf-8",
    )
    (temp_root / "src" / "conflict-entity.js").write_text(
        "export const ConflictingClass = THING.Entity\n",
        encoding="utf-8",
    )
    (temp_root / "src" / "conflict-app.js").write_text(
        "export const ConflictingClass = THING.App\n",
        encoding="utf-8",
    )
    (temp_root / "src" / "custom").mkdir()
    (temp_root / "src" / "custom" / "helper.ts").write_text(
        "export const configuredAliasEntity = new THING.Entity()\n",
        encoding="utf-8",
    )
    contract_path = temp_root / "resolver-contract.json"
    contract_path.write_text(json.dumps(make_structured_resolver_contract()), encoding="utf-8")
    alias_config = temp_root / "alias-config.json"
    alias_config.write_text(
        json.dumps({"compilerOptions": {"paths": {"@custom/*": ["src/custom/*"]}}}),
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
    completed = subprocess.run(
        [
            node,
            str(extractor),
            "--project-root",
            str(temp_root),
            "--parser-root",
            parser_root,
            "--output",
            str(output),
            "--contract",
            str(contract_path),
            "--alias-config",
            str(alias_config),
            "--entry",
            "src/main.js",
            "--entry",
            "src/broken.js",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    full_usage = json.loads(output.read_text(encoding="utf-8"))

    changed_files = temp_root / "changed-files.json"
    changed_files.write_text(json.dumps(["src/cross-module.js"]), encoding="utf-8")
    incremental_output = temp_root / "usage-incremental.json"
    subprocess.run(
        [
            node,
            str(extractor),
            "--project-root",
            str(temp_root),
            "--parser-root",
            parser_root,
            "--output",
            str(incremental_output),
            "--contract",
            str(contract_path),
            "--alias-config",
            str(alias_config),
            "--changed-files",
            str(changed_files),
            "--entry",
            "src/main.js",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    cache_path = temp_root / "resolver-cache.json"
    cached_first_output = temp_root / "usage-cache-first.json"
    cached_command = [
        node,
        str(extractor),
        "--project-root",
        str(temp_root),
        "--parser-root",
        parser_root,
        "--output",
        str(cached_first_output),
        "--contract",
        str(contract_path),
        "--alias-config",
        str(alias_config),
        "--entry",
        "src/main.js",
        "--entry",
        "src/broken.js",
        "--cache",
        str(cache_path),
    ]
    subprocess.run(cached_command, check=True, capture_output=True, text=True)
    cached_second_output = temp_root / "usage-cache-second.json"
    cached_second_command = [*cached_command]
    cached_second_command[cached_second_command.index("--output") + 1] = str(cached_second_output)
    subprocess.run(cached_second_command, check=True, capture_output=True, text=True)
    cached_usage = json.loads(cached_second_output.read_text(encoding="utf-8"))
    return full_usage, json.loads(incremental_output.read_text(encoding="utf-8")), cached_usage


def run_unconverged_module_flow(node: str, parser_root: str, temp_root: Path) -> dict:
    """构造超过固定传播轮次的 re-export 链，确认解析器以 gap 阻断而非静默漏报。"""

    chain_root = temp_root / "long-chain"
    (chain_root / "src").mkdir(parents=True)
    (chain_root / "index.html").write_text(
        '<script type="module" src="/src/main.js"></script>\n',
        encoding="utf-8",
    )
    (chain_root / "src" / "main.js").write_text(
        "import { EntityClass } from './a00.js'\nnew EntityClass()\n",
        encoding="utf-8",
    )
    for index in range(10):
        next_name = f"a{index + 1:02d}.js"
        (chain_root / "src" / f"a{index:02d}.js").write_text(
            f"export {{ EntityClass }} from './{next_name}'\n",
            encoding="utf-8",
        )
    (chain_root / "src" / "a10.js").write_text(
        "export const EntityClass = THING.Entity\n",
        encoding="utf-8",
    )
    output = chain_root / "usage.json"
    extractor = Path(__file__).resolve().parent / "extract_usage_surface.mjs"
    subprocess.run(
        [
            node,
            str(extractor),
            "--project-root",
            str(chain_root),
            "--parser-root",
            parser_root,
            "--output",
            str(output),
            "--entry",
            "src/main.js",
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
        usage, incremental_usage, cached_usage = run_usage_extractor(args.node, args.parser_root, temp_root)
        unconverged_usage = run_unconverged_module_flow(args.node, args.parser_root, temp_root)
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
    ambiguous = [entity for entity in entities if entity["resolution_status"] == "ambiguous"]
    assert len(dynamic) == 1 and dynamic[0]["production_reachable"] is True
    assert any("new ConflictingClass()" in entity["expression"] for entity in ambiguous)
    assert any("destructure:Entity->Entity" in entity["alias_provenance"] for entity in entities)
    assert any(
        entity["canonical_key"] == "method|THING.Entity|destroy"
        and "destructure:destroy->destroyEntity" in entity["alias_provenance"]
        for entity in entities
    )
    assert any(entity["canonical_key"] == "method|THING.Scene|load" for entity in entities)
    assert not any(
        entity["resolution_status"] == "ambiguous" and "Scene" in entity.get("expression", "")
        for entity in entities
    )
    assert usage["resolver"]["contract_return_types"] == "structured reference/Promise<reference> only"
    assert usage["resolver"]["alias_config"] == "explicit JSON profile"
    assert sum(
        entity["canonical_key"] == "method|THING.Entity|destroy"
        and any(item.startswith("import:") or item.startswith("import-namespace:") for item in entity["alias_provenance"])
        for entity in entities
    ) >= 2
    assert any(
        entity["canonical_key"] == "constructor|THING.Entity|constructor"
        and "new ImportedEntityClass()" in entity["expression"]
        for entity in entities
    )
    assert any(
        entity["canonical_key"] == "constructor|THING.App|constructor"
        and "new ReExportedApp()" in entity["expression"]
        for entity in entities
    )
    assert usage["incremental"]["complete_surface"] is True
    assert cached_usage["cache"]["hit"] is True
    assert len(cached_usage["cache"]["reused_files"]) == usage["summary"]["source_files"]
    assert cached_usage["usage_entities"] == usage["usage_entities"]
    assert cached_usage["summary"] == usage["summary"]
    assert incremental_usage["incremental"]["enabled"] is True
    assert incremental_usage["incremental"]["complete_surface"] is False
    assert incremental_usage["incremental"]["changed_files"] == ["src/cross-module.js"]
    assert "src/main.js" in incremental_usage["incremental"]["analyzed_files"]
    assert "src/consumer-exports.js" in incremental_usage["incremental"]["analyzed_files"]
    assert {
        entity["source"]["path"] for entity in incremental_usage["usage_entities"]
    } <= set(incremental_usage["incremental"]["analyzed_files"])
    assert any(
        entity["source"]["path"] == "src/main.js"
        for entity in incremental_usage["usage_entities"]
    )
    assert any(
        entity["resolution_status"] == "ambiguous"
        and "new ConflictingClass()" in entity["expression"]
        for entity in entities
    )
    assert any(
        entity["resolution_status"] == "ambiguous"
        and "makeEntity().destroy()" in entity["expression"]
        for entity in entities
    )
    assert any(
        entity["resolution_status"] == "ambiguous"
        and "makeArrowEntity().destroy()" in entity["expression"]
        for entity in entities
    )
    assert any(
        entity["resolution_status"] == "ambiguous"
        and "makeDefaultEntity().destroy()" in entity["expression"]
        for entity in entities
    )
    assert not any(
        "plainArrayHelper().map" in entity["expression"]
        for entity in entities
    )
    assert any(
        entity["resolution_status"] == "ambiguous"
        and "DynamicThingExports.EntityClass" in entity["expression"]
        for entity in entities
    )
    assert usage["resolver"]["module_flow_converged"] is True
    assert unconverged_usage["resolver"]["module_flow_converged"] is False
    assert any(
        gap["reason"] == "cross_module_resolution_incomplete"
        and gap["production_reachable"] is True
        for gap in unconverged_usage["reachability_gaps"]
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
    incremental_report = validate_all(contract, surface, incremental_usage, None)
    assert any(error["code"] == "incremental_surface_incomplete" for error in incremental_report["errors"])

    allowlist = {
        "entries": [
            {
                "status": "active",
                "artifact_set_id": FIXTURE_ARTIFACT_SET_ID,
                "usage_ids": [dynamic[0]["id"]],
                "dynamic_pattern": dynamic[0]["expression"],
                "reason": "Synthetic test exception.",
                "evidence_refs": ["fixture-evidence"],
            },
            *[
                {
                    "status": "active",
                    "artifact_set_id": FIXTURE_ARTIFACT_SET_ID,
                    "usage_ids": [entity["id"]],
                    "dynamic_pattern": entity["expression"],
                    "reason": "Synthetic ambiguous export exception.",
                    "evidence_refs": ["fixture-evidence"],
                }
                for entity in ambiguous
            ],
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
                    "contract_return_type_nested_owner",
                    "structured_method_return_nested_owner",
                    "explicit_alias_config_reachability",
                    "bounded_cross_module_named_default_namespace",
                    "bounded_reexport_chain",
                    "conflicting_reexport_ambiguous",
                    "factory_return_value_ambiguous",
                    "dynamic_import_value_flow_ambiguous",
                    "module_flow_convergence_reported",
                    "module_flow_nonconvergence_blocks",
                    "incremental_reverse_dependency_delta",
                    "incremental_delta_rejected_by_contract_gate",
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
