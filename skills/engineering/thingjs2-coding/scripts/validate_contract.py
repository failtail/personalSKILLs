#!/usr/bin/env python3
"""交叉校验 Versioned Contract、Runtime Surface 与 Project Usage Surface。"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from contract_signature_schema import (
    STRUCTURED_CONTRACT_SCHEMA_VERSION,
    STRUCTURED_SIGNATURE_SCHEMA_VERSION,
    has_structured_signature,
    validate_structured_signature,
)


ALLOWED_CONTRACT_STATES = {
    "documented",
    "existence_verified",
    "behavior_verified",
    "blocked",
}
SUPPORTED_CONTRACT_SCHEMA_VERSIONS = {2, STRUCTURED_CONTRACT_SCHEMA_VERSION}
ALLOWED_RESOLUTION_STATES = {
    "resolved",
    "resolved_inherited",
    "ambiguous",
    "dynamic_unresolved",
    "parse_failed",
}
ALLOWED_USAGE_STATES = {"allowed", "conditional", "blocked"}
ALLOWED_API_KINDS = {"constructor", "method", "property"}
ALLOWED_VERSION_RELATIONS = {"exact", "compatible_range", "unversioned_latest"}
PRODUCTION_BLOCKING_RESOLUTION_STATES = {"ambiguous", "dynamic_unresolved", "parse_failed"}


def parse_args() -> argparse.Namespace:
    """解析 CI 输入；Usage Surface 可省略以单独验证 Contract/Runtime。"""

    parser = argparse.ArgumentParser(description="Validate the ThingJS versioned Contract pipeline.")
    parser.add_argument("--contract", required=True)
    parser.add_argument("--runtime-surface", required=True)
    parser.add_argument("--usage-surface")
    parser.add_argument("--allowlist")
    parser.add_argument("--project-profile")
    parser.add_argument("--output")
    return parser.parse_args()


def read_json(path: str) -> dict[str, Any]:
    """读取 JSON 对象并保留路径错误为 CI 可见失败。"""

    resolved = Path(path).expanduser().resolve()
    data = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {resolved}")
    return data


def add_issue(
    collection: list[dict[str, Any]],
    code: str,
    path: str,
    message: str,
    **details: Any,
) -> None:
    """写入结构化问题，便于 CI 和 Skill 使用同一报告。"""

    issue = {"code": code, "path": path, "message": message}
    issue.update({key: value for key, value in details.items() if value is not None})
    collection.append(issue)


def official_source(source: dict[str, Any]) -> bool:
    """Contract 仅接受已登记的一方官方证据类型作为语义来源。"""

    source_type = source.get("source_type")
    if source_type in {"official_api", "official_documentation"}:
        return isinstance(source.get("url"), str) and bool(source["url"])
    if source_type == "context7_retrieval":
        return (
            source.get("provenance_checked") is True
            and isinstance(source.get("original_source_url"), str)
            and bool(source["original_source_url"])
        )
    return False


def runtime_index(surface: dict[str, Any]) -> tuple[set[tuple[str, str, str]], dict[tuple[str, str, str], set[str]]]:
    """建立存在性和继承 owner 映射；descriptor 不提供签名或行为结论。"""

    keys: set[tuple[str, str, str]] = set()
    inherited_owners: dict[tuple[str, str, str], set[str]] = {}
    for item in surface.get("constructors", []):
        owner = item.get("owner")
        if owner:
            keys.add(("constructor", owner, "constructor"))
    for item in surface.get("namespace_members", []):
        owner, member = item.get("owner"), item.get("member")
        if not owner or not member:
            continue
        kind = "method" if item.get("kind") == "method" else "property"
        keys.add((kind, owner, member))
    members_by_owner: dict[str, set[tuple[str, str]]] = {}
    for item in surface.get("prototype_members", []):
        effective = item.get("effective_owner")
        declared = item.get("declared_owner")
        member = item.get("member")
        if not effective or not member:
            continue
        kind = "method" if item.get("kind") == "method" else "property"
        keys.add((kind, effective, member))
        members_by_owner.setdefault(effective, set()).add((kind, member))
        if declared:
            keys.add((kind, declared, member))
            inherited_owners.setdefault((kind, effective, member), set()).add(declared)
    parents: dict[str, set[str]] = {}
    for item in surface.get("inheritance", []):
        if isinstance(item, dict) and item.get("child") and item.get("parent"):
            parents.setdefault(item["child"], set()).add(item["parent"])

    # Usage owner 可能是子类，而 Contract owner 是声明该成员的基类。
    for child in parents:
        queue = list(parents.get(child, set()))
        visited: set[str] = set()
        while queue:
            ancestor = queue.pop()
            if ancestor in visited:
                continue
            visited.add(ancestor)
            for kind, member in members_by_owner.get(ancestor, set()):
                inherited_owners.setdefault((kind, child, member), set()).add(ancestor)
            queue.extend(parents.get(ancestor, set()) - visited)
    return keys, inherited_owners


def artifact_map(binding: dict[str, Any]) -> dict[tuple[str, str], str]:
    """按 role/path 比较 Artifact Set，避免仅比较版本号掩盖插件漂移。"""

    result: dict[tuple[str, str], str] = {}
    for item in binding.get("artifacts", []):
        if isinstance(item, dict) and item.get("role") and item.get("path") and item.get("sha256"):
            result[(item["role"], item["path"])] = item["sha256"]
    return result


def computed_artifact_set_id(binding: dict[str, Any]) -> str | None:
    """按公共 role/path/SHA 规则重算身份，防止多个输入共享伪造 ID。"""

    artifacts = binding.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        return None
    normalized: list[tuple[str, str, str]] = []
    identities: set[tuple[str, str]] = set()
    for item in artifacts:
        if not isinstance(item, dict):
            return None
        role, path, sha256 = item.get("role"), item.get("path"), item.get("sha256")
        if not all(isinstance(value, str) and value for value in (role, path, sha256)):
            return None
        if len(sha256) != 64 or any(character not in "0123456789abcdefABCDEF" for character in sha256):
            return None
        if (role, path) in identities:
            return None
        identities.add((role, path))
        normalized.append((role, path, sha256))
    normalized.sort(key=lambda item: (item[0], item[1]))
    identity = "\n".join("|".join(item) for item in normalized)
    return f"sha256:{hashlib.sha256(identity.encode('utf-8')).hexdigest()}"


def profile_artifact_map(profile: dict[str, Any]) -> dict[tuple[str, str], str]:
    """把当前项目 Preflight 制品转换为与 Contract 相同的 role/path/SHA 键。"""

    result: dict[tuple[str, str], str] = {}
    for item in profile.get("sdk_artifacts", []):
        if not isinstance(item, dict) or not item.get("path") or not item.get("sha256"):
            continue
        name = Path(item["path"]).name.lower()
        if name == "thing.min.js":
            role = "core"
        elif "campus" in name:
            role = "campus"
        elif "earth" in name:
            role = "earth"
        else:
            role = name.removesuffix(".min.js").removesuffix(".js").replace(".", "-")
        result[(role, item["path"])] = item["sha256"]
    return result


def validate_artifact_binding(
    contract: dict[str, Any],
    surface: dict[str, Any],
    errors: list[dict[str, Any]],
    project_profile: dict[str, Any] | None = None,
) -> None:
    """任何核心或插件 SHA 漂移都必须先生成新的 Runtime Surface。"""

    contract_binding = contract.get("sdk_binding")
    surface_binding = surface.get("sdk_binding")
    if not isinstance(contract_binding, dict):
        add_issue(errors, "contract_sdk_binding", "sdk_binding", "Contract requires sdk_binding.")
        return
    if not isinstance(surface_binding, dict):
        add_issue(errors, "surface_sdk_binding", "runtime.sdk_binding", "Runtime Surface requires sdk_binding.")
        return


    for label, binding in (("contract", contract_binding), ("runtime", surface_binding)):
        computed_identity = computed_artifact_set_id(binding)
        if computed_identity is None:
            add_issue(
                errors,
                "artifact_set_invalid",
                f"{label}.sdk_binding.artifacts",
                "Artifact Set requires at least one complete role/path/SHA record.",
            )
        elif binding.get("artifact_set_id") != computed_identity:
            add_issue(
                errors,
                "artifact_set_identity",
                f"{label}.sdk_binding.artifact_set_id",
                "artifact_set_id does not match the normalized role/path/SHA records.",
                expected=computed_identity,
                actual=binding.get("artifact_set_id"),
            )

    capture = surface.get("capture")
    if not isinstance(capture, dict) or capture.get("mode") != "browser_descriptor_probe":
        add_issue(
            errors,
            "runtime_capture_mode",
            "runtime.capture",
            "Runtime Surface must come from the browser descriptor probe.",
        )
    elif not isinstance(capture.get("page_errors"), list) or capture.get("page_errors"):
        add_issue(
            errors,
            "runtime_capture_errors",
            "runtime.capture.page_errors",
            "A Runtime Surface with missing or non-empty browser page errors is invalid.",
        )
    if surface.get("runtime_version") != contract_binding.get("sdk_version"):
        add_issue(
            errors,
            "runtime_version_mismatch",
            "runtime.runtime_version",
            "Browser runtime version must equal the Contract SDK version.",
            runtime=surface.get("runtime_version"),
            contract=contract_binding.get("sdk_version"),
        )

    for field in ("sdk_version", "artifact_set_id"):
        if contract_binding.get(field) != surface_binding.get(field):
            add_issue(
                errors,
                "artifact_binding_mismatch",
                f"sdk_binding.{field}",
                f"Contract and Runtime Surface disagree on {field}.",
                contract=contract_binding.get(field),
                runtime=surface_binding.get(field),
            )
    if artifact_map(contract_binding) != artifact_map(surface_binding):
        add_issue(
            errors,
            "artifact_sha_mismatch",
            "sdk_binding.artifacts",
            "Contract and Runtime Surface artifact role/path/SHA sets differ.",
        )
    if project_profile is not None and artifact_map(contract_binding) != profile_artifact_map(project_profile):
        add_issue(
            errors,
            "project_artifact_drift",
            "project_profile.sdk_artifacts",
            "Current project artifacts differ from the pinned Contract; recapture Runtime Surface and review a new Contract.",
        )


def validate_contract_records(
    contract: dict[str, Any],
    runtime_keys: set[tuple[str, str, str]],
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> dict[tuple[str, str, str], dict[str, Any]]:
    """校验语义证据、存在性和行为分级，并返回 canonical key 索引。"""

    schema_version = contract.get("schema_version")
    if schema_version not in SUPPORTED_CONTRACT_SCHEMA_VERSIONS:
        add_issue(
            errors,
            "contract_schema_version",
            "schema_version",
            f"Unsupported Contract schema version: {schema_version}",
        )
    if schema_version == STRUCTURED_CONTRACT_SCHEMA_VERSION and contract.get("signature_schema_version") != STRUCTURED_SIGNATURE_SCHEMA_VERSION:
        add_issue(
            errors,
            "signature_schema_version",
            "signature_schema_version",
            "Structured Contract schema requires the supported signature schema version.",
        )

    records = contract.get("apis")
    if not isinstance(records, list):
        add_issue(errors, "contract_apis", "apis", "Contract requires an apis array.")
        return {}

    index: dict[tuple[str, str, str], dict[str, Any]] = {}
    for position, record in enumerate(records):
        record_path = f"apis[{position}]"
        if not isinstance(record, dict):
            add_issue(errors, "contract_record", record_path, "API Contract record must be an object.")
            continue
        key = (record.get("kind"), record.get("owner"), record.get("name"))
        if not all(isinstance(value, str) and value for value in key):
            add_issue(errors, "canonical_key", record_path, "kind, owner and name are required.")
            continue
        if record.get("kind") not in ALLOWED_API_KINDS:
            add_issue(
                errors,
                "api_kind",
                f"{record_path}.kind",
                f"Unsupported API kind: {record.get('kind')}",
            )
        if key in index:
            add_issue(errors, "duplicate_canonical_key", record_path, f"Duplicate canonical key: {key}")
            continue
        index[key] = record

        state = record.get("contract_state")
        if state not in ALLOWED_CONTRACT_STATES:
            add_issue(errors, "contract_state", f"{record_path}.contract_state", f"Unknown state: {state}")
        usage_state = record.get("usage_state")
        if usage_state not in ALLOWED_USAGE_STATES:
            add_issue(
                errors,
                "usage_state",
                f"{record_path}.usage_state",
                f"Unknown usage state: {usage_state}",
            )
        sources = record.get("sources")
        if not isinstance(sources, list) or not any(official_source(source) for source in sources if isinstance(source, dict)):
            add_issue(errors, "official_evidence_missing", f"{record_path}.sources", "API semantics require official evidence.")
            sources = []
        for source_index, source in enumerate(sources):
            if not isinstance(source, dict):
                continue
            relation = source.get("version_relation")
            if relation not in ALLOWED_VERSION_RELATIONS:
                add_issue(
                    errors,
                    "source_version_relation",
                    f"{record_path}.sources[{source_index}].version_relation",
                    f"Unknown source version relation: {relation}",
                )
            if relation in {"exact", "compatible_range"}:
                content_sha256 = source.get("content_sha256")
                if (
                    not isinstance(content_sha256, str)
                    or len(content_sha256) != 64
                    or any(character not in "0123456789abcdefABCDEF" for character in content_sha256)
                ):
                    add_issue(
                        errors,
                        "controlled_source_snapshot",
                        f"{record_path}.sources[{source_index}].content_sha256",
                        "Target-version controlled evidence requires a SHA-256 snapshot hash.",
                    )
            if relation == "unversioned_latest":
                add_issue(
                    warnings,
                    "stale_review",
                    f"{record_path}.sources[{source_index}]",
                    "Unversioned latest official evidence requires review but does not block the pinned SDK Contract.",
                    url=source.get("url"),
                )

        for conflict_index, conflict in enumerate(record.get("evidence_conflicts", [])):
            if not isinstance(conflict, dict) or conflict.get("status") != "mismatch":
                continue
            relation = conflict.get("version_relation")
            conflict_path = f"{record_path}.evidence_conflicts[{conflict_index}]"
            if relation == "unversioned_latest":
                add_issue(
                    warnings,
                    "stale_review",
                    conflict_path,
                    "A latest-only semantic mismatch requires review and cannot block the pinned Contract by itself.",
                    evidence_ref=conflict.get("evidence_ref"),
                )
            elif relation in {"exact", "compatible_range"} and state != "blocked":
                add_issue(
                    errors,
                    "controlled_evidence_mismatch_not_blocked",
                    conflict_path,
                    "A controlled target-version mismatch requires contract_state=blocked.",
                    evidence_ref=conflict.get("evidence_ref"),
                )
        signatures = record.get("signatures")
        has_controlled_signature = isinstance(signatures, list) and any(
            isinstance(signature, dict)
            and isinstance(signature.get("text"), str)
            and bool(signature["text"].strip())
            and isinstance(signature.get("source_refs"), list)
            and bool(signature["source_refs"])
            for signature in signatures
        )
        if usage_state == "allowed" and not has_controlled_signature:
            add_issue(
                errors,
                "signature_missing",
                f"{record_path}.signatures",
                "Allowed API requires a non-empty controlled signature and source references.",
            )
        if isinstance(signatures, list):
            for signature_index, signature in enumerate(signatures):
                if has_structured_signature(signature):
                    structured_errors = validate_structured_signature(
                        signature,
                        f"{record_path}.signatures[{signature_index}]",
                        record.get("kind", ""),
                    )
                    for structured_error in structured_errors:
                        add_issue(
                            errors,
                            "structured_signature_invalid",
                            structured_error["path"],
                            structured_error["message"],
                        )

        exists_now = key in runtime_keys
        if state in {"existence_verified", "behavior_verified"}:
            existence = record.get("existence_evidence")
            expected_artifact_set = contract.get("sdk_binding", {}).get("artifact_set_id")
            if (
                not isinstance(existence, dict)
                or existence.get("status") != "supported"
                or existence.get("artifact_set_id") != expected_artifact_set
            ):
                add_issue(
                    errors,
                    "existence_evidence_binding",
                    f"{record_path}.existence_evidence",
                    "Verified existence requires supported evidence bound to the Contract Artifact Set.",
                )
        if state in {"existence_verified", "behavior_verified"} and not exists_now:
            add_issue(
                errors,
                "runtime_member_missing",
                record_path,
                "Contract claims runtime existence but the bound Runtime Surface does not contain the member.",
                canonical_key="|".join(key),
            )
        if state == "documented" and exists_now:
            add_issue(
                warnings,
                "existence_not_promoted",
                record_path,
                "Runtime member exists but Contract has not promoted the existence evidence.",
            )

        if state == "behavior_verified":
            artifact_set_id = contract.get("sdk_binding", {}).get("artifact_set_id")
            passing_behavior = any(
                isinstance(item, dict)
                and item.get("status") == "passed"
                and item.get("artifact_set_id") == artifact_set_id
                and item.get("test_ref")
                and item.get("scenario")
                for item in record.get("behavior_evidence", [])
            )
            if not passing_behavior:
                add_issue(
                    errors,
                    "behavior_evidence_missing",
                    f"{record_path}.behavior_evidence",
                    "behavior_verified requires a passed scenario bound to the exact Artifact Set.",
                )

        failed_behavior = any(
            isinstance(item, dict)
            and item.get("status") in {"failed", "conflict"}
            and item.get("artifact_set_id") == contract.get("sdk_binding", {}).get("artifact_set_id")
            for item in record.get("behavior_evidence", [])
        )
        if failed_behavior and state != "blocked":
            add_issue(
                errors,
                "failed_behavior_not_blocked",
                f"{record_path}.behavior_evidence",
                "A failed behavior test for the bound Artifact Set requires contract_state=blocked.",
            )

        for test_index, behavior in enumerate(record.get("required_behavior_tests", [])):
            if not isinstance(behavior, dict) or behavior.get("status") != "passed":
                add_issue(
                    errors,
                    "required_behavior_test",
                    f"{record_path}.required_behavior_tests[{test_index}]",
                    "A release-required Runtime Behavior Test has not passed.",
                )
    return index


def active_allowlist_entries(allowlist: dict[str, Any] | None, artifact_set_id: str) -> list[dict[str, Any]]:
    """只使用与当前 Artifact Set 精确绑定且具理由和证据的 allowlist。"""

    if not allowlist:
        return []
    result = []
    for item in allowlist.get("entries", []):
        if not isinstance(item, dict):
            continue
        if item.get("status") != "active" or item.get("artifact_set_id") != artifact_set_id:
            continue
        if not item.get("reason") or not item.get("evidence_refs") or not item.get("dynamic_pattern"):
            continue
        usage_ids = item.get("usage_ids", [])
        if not isinstance(usage_ids, list) or not usage_ids:
            continue
        if any(not isinstance(usage_id, str) or not usage_id for usage_id in usage_ids):
            continue
        result.append(item)
    return result


def usage_allowlisted(entity: dict[str, Any], entries: list[dict[str, Any]]) -> bool:
    """匹配精确 Usage ID 或明确源码范围；宽泛通配不能跨 Artifact Set。"""

    for item in entries:
        scope_matches = entity.get("id") in item.get("usage_ids", [])
        if scope_matches and entity.get("expression", "") == item["dynamic_pattern"]:
            return True
    return False


def match_contract_record(
    entity: dict[str, Any],
    contract_index: dict[tuple[str, str, str], dict[str, Any]],
    inherited_owners: dict[tuple[str, str, str], set[str]],
) -> tuple[dict[str, Any] | None, str]:
    """先匹配直接 owner，再用 Runtime 继承图解析规范声明 owner。"""

    raw_key = entity.get("canonical_key")
    if not isinstance(raw_key, str):
        return None, "unresolved"
    parts = raw_key.split("|", 2)
    if len(parts) != 3:
        return None, "unresolved"
    key = tuple(parts)
    if key in contract_index:
        return contract_index[key], "direct"
    kind, effective_owner, member = key
    for declared_owner in inherited_owners.get((kind, effective_owner, member), set()):
        inherited_key = (kind, declared_owner, member)
        if inherited_key in contract_index:
            return contract_index[inherited_key], "inherited"
    return None, "missing"


def validate_usage(
    usage: dict[str, Any],
    contract: dict[str, Any],
    contract_index: dict[tuple[str, str, str], dict[str, Any]],
    inherited_owners: dict[tuple[str, str, str], set[str]],
    allowlist: dict[str, Any] | None,
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> None:
    """生产可达的未解析使用默认阻断，Regex discovery 永不生成通过结论。"""

    artifact_set_id = contract.get("sdk_binding", {}).get("artifact_set_id", "")
    allowed_dynamic = active_allowlist_entries(allowlist, artifact_set_id)
    reachable_files = set(usage.get("reachable_files", []))

    for gap_index, gap in enumerate(usage.get("reachability_gaps", [])):
        target = errors if gap.get("production_reachable") is True else warnings
        add_issue(
            target,
            "production_reachability_gap" if target is errors else "nonproduction_reachability_gap",
            f"reachability_gaps[{gap_index}]",
            "Static production reachability is incomplete for this import edge.",
            reason=gap.get("reason"),
            specifier=gap.get("specifier"),
            source=gap.get("source"),
        )

    for failure_index, failure in enumerate(usage.get("parse_failures", [])):
        target = errors if failure.get("path") in reachable_files else warnings
        add_issue(
            target,
            "production_parse_failure" if target is errors else "nonproduction_parse_failure",
            f"parse_failures[{failure_index}]",
            "AST parse failure prevents authoritative Usage analysis.",
            source=failure.get("path"),
        )

    for position, entity in enumerate(usage.get("usage_entities", [])):
        entity_path = f"usage_entities[{position}]"
        state = entity.get("resolution_status")
        if state not in ALLOWED_RESOLUTION_STATES:
            add_issue(errors, "usage_resolution_state", entity_path, f"Unknown resolution state: {state}")
            continue
        production = entity.get("production_reachable") is True
        if state in PRODUCTION_BLOCKING_RESOLUTION_STATES:
            if production and not usage_allowlisted(entity, allowed_dynamic):
                add_issue(
                    errors,
                    "dynamic_usage_blocked",
                    entity_path,
                    "Production-reachable unresolved ThingJS usage requires an artifact-bound allowlist.",
                    usage_id=entity.get("id"),
                    source=entity.get("source"),
                )
            else:
                add_issue(
                    warnings,
                    "dynamic_usage_review",
                    entity_path,
                    "Unresolved ThingJS usage is non-production or explicitly allowlisted.",
                    usage_id=entity.get("id"),
                )
            continue

        record, match_mode = match_contract_record(entity, contract_index, inherited_owners)
        if record is None:
            target = errors if production else warnings
            add_issue(
                target,
                "usage_not_in_contract",
                entity_path,
                "ThingJS Usage Entity is absent from the pinned Contract.",
                canonical_key=entity.get("canonical_key"),
                source=entity.get("source"),
            )
            continue
        if record.get("usage_state") == "blocked" or record.get("contract_state") == "blocked":
            add_issue(
                errors if production else warnings,
                "blocked_api_usage",
                entity_path,
                "Project code uses an API blocked by the current Contract.",
                contract_id=record.get("id"),
            )
        elif production and record.get("contract_state") == "documented":
            add_issue(
                errors,
                "usage_without_existence_evidence",
                entity_path,
                "Production usage requires Runtime Surface existence evidence.",
                contract_id=record.get("id"),
            )
        if match_mode == "inherited":
            entity["contract_resolution"] = "resolved_inherited"
            entity["contract_id"] = record.get("id")

    for position, finding in enumerate(usage.get("discovery_findings", [])):
        add_issue(
            warnings,
            "regex_discovery_only",
            f"discovery_findings[{position}]",
            "Regex found a ThingJS-shaped token that is not a verified Usage Entity.",
            token=finding.get("token"),
            source=finding.get("source"),
        )


def validate_all(
    contract: dict[str, Any],
    surface: dict[str, Any],
    usage: dict[str, Any] | None,
    allowlist: dict[str, Any] | None,
    project_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """返回完整报告；stale/review 告警不会被升级为版本绑定失败。"""

    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    if contract.get("schema_version") not in SUPPORTED_CONTRACT_SCHEMA_VERSIONS:
        add_issue(
            errors,
            "contract_schema",
            "schema_version",
            f"Contract schema_version must be one of {sorted(SUPPORTED_CONTRACT_SCHEMA_VERSIONS)}.",
        )
    if surface.get("schema_version") != 1:
        add_issue(errors, "surface_schema", "runtime.schema_version", "Runtime Surface schema_version must equal 1.")

    validate_artifact_binding(contract, surface, errors, project_profile)
    runtime_keys, inherited_owners = runtime_index(surface)
    contract_index = validate_contract_records(contract, runtime_keys, errors, warnings)
    if usage is not None:
        if usage.get("schema_version") != 1:
            add_issue(errors, "usage_schema", "usage.schema_version", "Usage Surface schema_version must equal 1.")
        validate_usage(
            usage,
            contract,
            contract_index,
            inherited_owners,
            allowlist,
            errors,
            warnings,
        )
    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "contract_apis": len(contract_index),
            "runtime_members": len(runtime_keys),
            "usage_entities": len(usage.get("usage_entities", [])) if usage else 0,
            "errors": len(errors),
            "warnings": len(warnings),
        },
    }


def main() -> int:
    """输出机器报告并用非零退出码守住发布边界。"""

    args = parse_args()
    try:
        contract = read_json(args.contract)
        surface = read_json(args.runtime_surface)
        usage = read_json(args.usage_surface) if args.usage_surface else None
        allowlist = read_json(args.allowlist) if args.allowlist else None
        project_profile = read_json(args.project_profile) if args.project_profile else None
        report = validate_all(contract, surface, usage, allowlist, project_profile)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        report = {
            "valid": False,
            "errors": [{"code": "load_error", "path": "$", "message": str(error)}],
            "warnings": [],
            "summary": {"contract_apis": 0, "runtime_members": 0, "usage_entities": 0, "errors": 1, "warnings": 0},
        }

    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
    sys.stdout.write(payload)
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
