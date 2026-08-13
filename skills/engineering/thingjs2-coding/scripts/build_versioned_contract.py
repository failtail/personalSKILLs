#!/usr/bin/env python3
"""将旧版选择性 API Cache 规范化为绑定 SDK 制品集合的 JSON Contract。"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 2


def parse_args() -> argparse.Namespace:
    """解析输入证据；构建过程不修改原 Registry 或项目文件。"""

    parser = argparse.ArgumentParser(description="Build a versioned ThingJS JSON Contract.")
    parser.add_argument("--registry", required=True, help="Legacy selective API Registry JSON.")
    parser.add_argument("--project-profile", required=True, help="Preflight project profile JSON.")
    parser.add_argument("--runtime-surface", required=True, help="Browser Runtime Surface JSON.")
    parser.add_argument("--output", required=True, help="Versioned Contract output JSON.")
    return parser.parse_args()


def read_json(path: str) -> dict[str, Any]:
    """读取 JSON 对象并拒绝非对象根，避免把错误输入静默规范化。"""

    resolved = Path(path).expanduser().resolve()
    data = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {resolved}")
    return data


def artifact_role(relative_path: str) -> str:
    """从公开文件名给制品分配稳定角色；未知插件保留独立角色。"""

    name = Path(relative_path).name.lower()
    if name == "thing.min.js":
        return "core"
    if "campus" in name:
        return "campus"
    if "earth" in name:
        return "earth"
    return name.removesuffix(".min.js").removesuffix(".js").replace(".", "-")


def build_artifact_set(profile: dict[str, Any]) -> tuple[str, str, list[dict[str, Any]]]:
    """以有序角色、路径和 SHA 生成可复现的 SDK Artifact Set 身份。"""

    source_artifacts = profile.get("sdk_artifacts")
    if not isinstance(source_artifacts, list) or not source_artifacts:
        raise ValueError("Project profile contains no SDK artifacts.")

    artifacts: list[dict[str, Any]] = []
    versions: set[str] = set()
    for source in source_artifacts:
        if not isinstance(source, dict) or not source.get("path") or not source.get("sha256"):
            raise ValueError("Every SDK artifact requires path and sha256.")
        if source.get("version"):
            versions.add(source["version"])
        artifacts.append(
            {
                "role": artifact_role(source["path"]),
                "path": source["path"],
                "sha256": source["sha256"],
                "bytes": source.get("bytes"),
                "version": source.get("version"),
                "compile_time": source.get("compile_time"),
                "sdk_git_commit": source.get("sdk_git_commit"),
            }
        )
    artifacts.sort(key=lambda item: (item["role"], item["path"]))
    if len(versions) != 1:
        raise ValueError(f"Expected one exact SDK version across artifacts, found: {sorted(versions)}")

    identity = "\n".join(
        f"{item['role']}|{item['path']}|{item['sha256']}" for item in artifacts
    )
    artifact_set_id = f"sha256:{hashlib.sha256(identity.encode('utf-8')).hexdigest()}"
    return versions.pop(), artifact_set_id, artifacts


def runtime_match(record: dict[str, Any], surface: dict[str, Any]) -> list[dict[str, Any]]:
    """匹配存在性证据，不从 descriptor 反推参数、返回值或行为。"""

    owner = record.get("owner")
    name = record.get("name")
    kind = record.get("kind")
    matches: list[dict[str, Any]] = []

    if kind == "constructor":
        for candidate in surface.get("constructors", []):
            if candidate.get("owner") == owner:
                matches.append(
                    {
                        "runtime_path": candidate.get("runtime_path"),
                        "runtime_kind": "constructor",
                        "effective_owner": owner,
                        "declared_owner": owner,
                    }
                )
        return matches

    def compatible_member_kind(runtime_kind: str | None) -> bool:
        """Descriptor kind must agree; same-name accessor cannot prove a method."""

        if kind == "method":
            return runtime_kind == "method"
        if kind == "property":
            return runtime_kind in {"property", "accessor"}
        return False

    for candidate in surface.get("prototype_members", []):
        if candidate.get("member") != name:
            continue
        if not compatible_member_kind(candidate.get("kind")):
            continue
        if candidate.get("effective_owner") == owner or candidate.get("declared_owner") == owner:
            matches.append(
                {
                    "runtime_path": candidate.get("runtime_path"),
                    "runtime_kind": candidate.get("kind"),
                    "effective_owner": candidate.get("effective_owner"),
                    "declared_owner": candidate.get("declared_owner"),
                }
            )
    for candidate in surface.get("namespace_members", []):
        if (
            candidate.get("owner") == owner
            and candidate.get("member") == name
            and compatible_member_kind(candidate.get("kind"))
        ):
            matches.append(
                {
                    "runtime_path": candidate.get("runtime_path"),
                    "runtime_kind": candidate.get("kind"),
                    "effective_owner": owner,
                    "declared_owner": owner,
                }
            )
    return matches


def normalize_source(source: dict[str, Any], sdk_version: str) -> dict[str, Any]:
    """保留原证据并显式区分精确版本证据与无法定版的 latest 页面。"""

    normalized = dict(source)
    declared_relation = source.get("version_relation")
    version_evidence = str(source.get("version_evidence") or "")
    if declared_relation in {"exact", "compatible_range", "unversioned_latest"}:
        version_relation = declared_relation
    elif sdk_version in version_evidence:
        version_relation = "exact"
    else:
        version_relation = "unversioned_latest"
    review_state = "stale_review" if version_relation == "unversioned_latest" else "current"
    normalized.update(
        {
            "version_relation": version_relation,
            "review_state": review_state,
            "content_sha256": source.get("content_sha256"),
        }
    )
    return normalized


def normalize_record(
    record: dict[str, Any],
    sdk_version: str,
    artifact_set_id: str,
    surface: dict[str, Any],
) -> dict[str, Any]:
    """生成 Contract 记录，同时把存在性和行为证据保持为两个维度。"""

    normalized = dict(record)
    sources = [normalize_source(source, sdk_version) for source in record.get("sources", [])]
    matches = runtime_match(record, surface)
    legacy_runtime_verifications = record.get("runtime_verifications", [])
    behavior_evidence = [
        dict(item)
        for item in record.get("behavior_evidence", [])
        if isinstance(item, dict)
    ]
    evidence_conflicts = [
        dict(item)
        for item in record.get("evidence_conflicts", [])
        if isinstance(item, dict)
    ]
    controlled_mismatch = any(
        item.get("status") == "mismatch"
        and item.get("version_relation") in {"exact", "compatible_range"}
        for item in evidence_conflicts
    )
    failed_behavior = any(
        item.get("status") in {"failed", "conflict"}
        and item.get("artifact_set_id") == artifact_set_id
        for item in behavior_evidence
    )
    has_conflict = record.get("usage_state") == "blocked" or any(
        item.get("status") == "conflict"
        for item in legacy_runtime_verifications
        if isinstance(item, dict)
    ) or controlled_mismatch or failed_behavior
    behavior_supported = any(
        item.get("status") == "passed"
        and item.get("artifact_set_id") == artifact_set_id
        and item.get("test_ref")
        and item.get("scenario")
        for item in behavior_evidence
    )

    if has_conflict:
        contract_state = "blocked"
    elif behavior_supported and matches:
        contract_state = "behavior_verified"
    elif matches:
        contract_state = "existence_verified"
    else:
        contract_state = "documented"

    normalized.update(
        {
            "version_scope": sdk_version,
            "version_binding": {
                "sdk_version": sdk_version,
                "artifact_set_id": artifact_set_id,
            },
            "contract_state": contract_state,
            "sources": sources,
            "existence_evidence": {
                "status": "supported" if matches else "not_observed",
                "artifact_set_id": artifact_set_id,
                "surface_schema_version": surface.get("schema_version"),
                "matches": matches,
                "proves": "member_existence_only",
            },
            # 旧 Cache 的 runtime_verifications 缺少行为场景与 Artifact Set 绑定，
            # 只能作为迁移审计信息，不能自动晋级 behavior_verified。
            "legacy_runtime_verifications": legacy_runtime_verifications,
            "evidence_conflicts": evidence_conflicts,
            "behavior_evidence": behavior_evidence,
        }
    )
    return normalized


def build_contract(
    registry: dict[str, Any],
    profile: dict[str, Any],
    surface: dict[str, Any],
) -> dict[str, Any]:
    """构造机器消费 Contract；原始事实仍由受控官方证据和 Runtime 证据提供。"""

    sdk_version, artifact_set_id, artifacts = build_artifact_set(profile)
    surface_artifact_set_id = surface.get("sdk_binding", {}).get("artifact_set_id")
    if surface_artifact_set_id and surface_artifact_set_id != artifact_set_id:
        raise ValueError("Runtime Surface artifact_set_id does not match the project profile.")

    records = registry.get("apis")
    if not isinstance(records, list):
        raise ValueError("Legacy registry requires an apis array.")
    apis = [normalize_record(record, sdk_version, artifact_set_id, surface) for record in records]
    stale_sources = sorted(
        {
            source.get("url")
            for record in apis
            for source in record.get("sources", [])
            if source.get("review_state") == "stale_review" and source.get("url")
        }
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "contract_id": f"thingjs-{sdk_version}-{artifact_set_id.split(':', 1)[1][:16]}",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "sdk_binding": {
            "sdk_version": sdk_version,
            "artifact_set_id": artifact_set_id,
            "artifacts": artifacts,
        },
        "evidence_policy": {
            "machine_consumption_entry": "this_contract",
            "api_semantics": "controlled_official_evidence",
            "member_existence": "browser_runtime_surface",
            "runtime_behavior": "independent_runtime_behavior_test",
            "unversioned_latest_mismatch": "stale_review_only",
            "engineer_material": "recipe_faq_incident_only",
        },
        "stale_review_sources": stale_sources,
        "apis": apis,
    }


def main() -> int:
    """写入确定性 Contract，并输出版本、制品集合和记录数量摘要。"""

    args = parse_args()
    contract = build_contract(
        read_json(args.registry),
        read_json(args.project_profile),
        read_json(args.runtime_surface),
    )
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "contract_id": contract["contract_id"],
                "sdk_version": contract["sdk_binding"]["sdk_version"],
                "artifact_set_id": contract["sdk_binding"]["artifact_set_id"],
                "api_count": len(contract["apis"]),
                "stale_review_sources": len(contract["stale_review_sources"]),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
