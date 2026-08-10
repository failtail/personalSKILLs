#!/usr/bin/env python3
"""校验 ThingJS 2.0 Lightweight API Cache 的安全边界。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ALLOWED_EVIDENCE_LABELS = {
    "historical_incident",
    "internal_only",
    "official_unversioned",
    "official_verified",
    "project_verified",
    "runtime_conflict",
    "runtime_verified",
    "unit_verified",
    "unverified",
}
ALLOWED_USAGE_STATES = {"allowed", "blocked", "conditional"}
ALLOWED_RUNTIME_STATES = {"conflict", "inconclusive", "not_tested", "supported"}
ALLOWED_INCLUSION_REASONS = {
    "conflict",
    "frequent",
    "hallucination_history",
    "high_risk",
    "used",
    "verified",
}
ALLOWED_RETRIEVAL_CHANNELS = {
    "context7",
    "official_web",
    "local_knowledge",
    "project_runtime",
    "unit_test",
}
ALLOWED_CONTEXT7_LIBRARIES = {
    "/websites/cdn_uino_cn_thingjs_apidocs",
    "/websites/thingjs_new",
}
OFFICIAL_SOURCE_TYPES = {"official_api", "official_docs"}
OFFICIAL_HOSTS = {"cdn.uino.cn", "docs.thingjs.com", "thingjs.org.cn", "www.thingjs.org.cn"}
REQUIRED_RECORD_FIELDS = {
    "evidence_labels",
    "id",
    "inclusion_reason",
    "kind",
    "name",
    "owner",
    "project_status",
    "retrieval_channels",
    "signatures",
    "sources",
    "summary",
    "last_verified",
    "usage_state",
    "version_scope",
}


def parse_args() -> argparse.Namespace:
    """解析待校验 Registry 路径。"""

    parser = argparse.ArgumentParser(description="Validate a ThingJS 2.0 canonical API registry.")
    parser.add_argument("registry", help="Path to registry JSON.")
    return parser.parse_args()


def add_error(errors: list[dict[str, str]], code: str, path: str, message: str) -> None:
    """添加稳定的机器可读错误，供构建或 Agent 精确定位。"""

    errors.append({"code": code, "path": path, "message": message})


def is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def has_official_source(sources: list[Any]) -> bool:
    """确认来源类型、域名和 Context7 provenance 同时满足官方入口。"""

    for source in sources:
        if not isinstance(source, dict):
            continue
        url = source.get("url")
        if source.get("source_type") in OFFICIAL_SOURCE_TYPES:
            if is_non_empty_string(url) and urlparse(url).hostname in OFFICIAL_HOSTS:
                return True
        if (
            source.get("retrieval_channel") == "context7"
            and source.get("context7_library_id") in ALLOWED_CONTEXT7_LIBRARIES
            and source.get("provenance_checked") is True
            and is_non_empty_string(source.get("original_source_url"))
            and urlparse(source["original_source_url"]).hostname in OFFICIAL_HOSTS
        ):
            return True
    return False


def validate_record(
    record: Any,
    index: int,
    errors: list[dict[str, str]],
    ids: set[str],
    canonical_keys: set[tuple[str, str, str]],
) -> None:
    """验证单条缓存记录的选入理由、来源链和项目阻断不变量。"""

    path = f"apis[{index}]"
    if not isinstance(record, dict):
        add_error(errors, "record_type", path, "API record must be an object.")
        return

    missing = sorted(REQUIRED_RECORD_FIELDS - record.keys())
    if missing:
        add_error(errors, "missing_fields", path, f"Missing required fields: {', '.join(missing)}")

    record_id = record.get("id")
    if not is_non_empty_string(record_id):
        add_error(errors, "invalid_id", f"{path}.id", "ID must be a non-empty string.")
    elif record_id in ids:
        add_error(errors, "duplicate_id", f"{path}.id", f"Duplicate canonical ID: {record_id}")
    else:
        ids.add(record_id)

    owner = record.get("owner")
    name = record.get("name")
    kind = record.get("kind")
    if all(is_non_empty_string(value) for value in (kind, owner, name)):
        canonical_key = (kind, owner, name)
        if canonical_key in canonical_keys:
            add_error(
                errors,
                "duplicate_canonical_key",
                path,
                f"Duplicate kind + owner + name: {kind} + {owner} + {name}",
            )
        else:
            canonical_keys.add(canonical_key)

    version_scope = record.get("version_scope")
    if not is_non_empty_string(version_scope) or not version_scope.startswith("2"):
        add_error(errors, "invalid_version_scope", f"{path}.version_scope", "Only ThingJS 2.x is allowed.")

    inclusion_reason = record.get("inclusion_reason")
    if not isinstance(inclusion_reason, list) or not inclusion_reason:
        add_error(errors, "invalid_inclusion_reason", f"{path}.inclusion_reason", "At least one cache inclusion reason is required.")
    else:
        unknown_reasons = sorted(set(inclusion_reason) - ALLOWED_INCLUSION_REASONS)
        if unknown_reasons:
            add_error(
                errors,
                "unknown_inclusion_reason",
                f"{path}.inclusion_reason",
                f"Unknown reasons: {', '.join(unknown_reasons)}",
            )

    retrieval_channels = record.get("retrieval_channels")
    if not isinstance(retrieval_channels, list) or not retrieval_channels:
        add_error(errors, "invalid_retrieval_channels", f"{path}.retrieval_channels", "At least one retrieval channel is required.")
    else:
        unknown_channels = sorted(set(retrieval_channels) - ALLOWED_RETRIEVAL_CHANNELS)
        if unknown_channels:
            add_error(
                errors,
                "unknown_retrieval_channel",
                f"{path}.retrieval_channels",
                f"Unknown channels: {', '.join(unknown_channels)}",
            )

    for field in ("project_status", "last_verified"):
        if not is_non_empty_string(record.get(field)):
            add_error(errors, "cache_field", f"{path}.{field}", "Cache field must be a non-empty string.")

    evidence_labels = record.get("evidence_labels")
    if not isinstance(evidence_labels, list) or not evidence_labels:
        add_error(errors, "invalid_evidence", f"{path}.evidence_labels", "At least one evidence label is required.")
        evidence_labels = []
    else:
        unknown_labels = sorted(set(evidence_labels) - ALLOWED_EVIDENCE_LABELS)
        if unknown_labels:
            add_error(
                errors,
                "unknown_evidence_label",
                f"{path}.evidence_labels",
                f"Unknown labels: {', '.join(unknown_labels)}",
            )

    usage_state = record.get("usage_state")
    if usage_state not in ALLOWED_USAGE_STATES:
        add_error(errors, "invalid_usage_state", f"{path}.usage_state", "Usage state must be allowed, conditional, or blocked.")

    sources = record.get("sources")
    if not isinstance(sources, list):
        add_error(errors, "invalid_sources", f"{path}.sources", "Sources must be an array.")
        sources = []

    source_refs: set[str] = set()
    for source_index, source in enumerate(sources):
        source_path = f"{path}.sources[{source_index}]"
        if not isinstance(source, dict):
            add_error(errors, "source_type", source_path, "Source must be an object.")
            continue
        for field in ("ref", "source_id", "source_type", "url", "retrieved_at"):
            if not is_non_empty_string(source.get(field)):
                add_error(errors, "source_field", f"{source_path}.{field}", "Source field must be a non-empty string.")
        if is_non_empty_string(source.get("ref")):
            if source["ref"] in source_refs:
                add_error(errors, "duplicate_source_ref", f"{source_path}.ref", f"Duplicate source ref: {source['ref']}")
            source_refs.add(source["ref"])
        if source.get("retrieval_channel") == "context7":
            library_id = source.get("context7_library_id")
            if library_id not in ALLOWED_CONTEXT7_LIBRARIES:
                add_error(
                    errors,
                    "context7_library_unapproved",
                    f"{source_path}.context7_library_id",
                    "Context7 source must use an approved ThingJS library ID.",
                )
            original_url = source.get("original_source_url")
            if not is_non_empty_string(original_url):
                add_error(
                    errors,
                    "context7_original_source_missing",
                    f"{source_path}.original_source_url",
                    "Context7 retrieval requires the underlying official source URL.",
                )
            elif urlparse(original_url).hostname not in OFFICIAL_HOSTS:
                add_error(
                    errors,
                    "context7_original_source_unapproved",
                    f"{source_path}.original_source_url",
                    "Context7 original_source_url must use an approved official host.",
                )

    signatures = record.get("signatures")
    if not isinstance(signatures, list):
        add_error(errors, "invalid_signatures", f"{path}.signatures", "Signatures must be an array.")
        signatures = []
    for signature_index, signature in enumerate(signatures):
        signature_path = f"{path}.signatures[{signature_index}]"
        if not isinstance(signature, dict) or not is_non_empty_string(signature.get("text")):
            add_error(errors, "signature_text", signature_path, "Signature must contain non-empty text.")
            continue
        refs = signature.get("source_refs")
        if not isinstance(refs, list) or not refs:
            add_error(errors, "signature_sources", f"{signature_path}.source_refs", "Signature requires source refs.")
        else:
            for ref in refs:
                if ref not in source_refs:
                    add_error(errors, "unknown_source_ref", f"{signature_path}.source_refs", f"Unknown source ref: {ref}")

    runtime_conflict = "runtime_conflict" in evidence_labels
    runtime_verifications = record.get("runtime_verifications", [])
    if not isinstance(runtime_verifications, list):
        add_error(errors, "runtime_verifications", f"{path}.runtime_verifications", "Runtime verifications must be an array.")
        runtime_verifications = []
    for runtime_index, verification in enumerate(runtime_verifications):
        runtime_path = f"{path}.runtime_verifications[{runtime_index}]"
        if not isinstance(verification, dict):
            add_error(errors, "runtime_type", runtime_path, "Runtime verification must be an object.")
            continue
        status = verification.get("status")
        if status not in ALLOWED_RUNTIME_STATES:
            add_error(errors, "runtime_status", f"{runtime_path}.status", "Unknown runtime verification status.")
        if status == "conflict":
            runtime_conflict = True

    official = has_official_source(sources)
    if "official_verified" in evidence_labels and not official:
        add_error(errors, "official_evidence_missing", path, "official_verified requires an approved official source URL.")
    if "official_verified" in evidence_labels:
        for source in sources:
            if source.get("retrieval_channel") == "context7" and source.get("provenance_checked") is not True:
                add_error(
                    errors,
                    "context7_provenance_missing",
                    path,
                    "Context7-backed official evidence requires provenance_checked=true.",
                )
    if usage_state == "allowed":
        if not official:
            add_error(errors, "allowed_without_official", path, "Allowed API requires an approved official source.")
        if not signatures:
            add_error(errors, "allowed_without_signature", path, "Allowed API requires at least one verified signature.")
        if runtime_conflict:
            add_error(errors, "runtime_conflict_leak", path, "API with a runtime conflict must be blocked.")
    if runtime_conflict and usage_state != "blocked":
        add_error(errors, "conflict_not_blocked", path, "Runtime conflict requires usage_state=blocked.")


def validate_registry(data: Any) -> dict[str, Any]:
    """返回完整错误列表，避免调用方反复修复单个问题。"""

    errors: list[dict[str, str]] = []
    if not isinstance(data, dict):
        add_error(errors, "root_type", "$", "Registry root must be an object.")
        return {"valid": False, "api_count": 0, "errors": errors}
    if data.get("schema_version") != 1:
        add_error(errors, "schema_version", "schema_version", "schema_version must equal 1.")
    apis = data.get("apis")
    if not isinstance(apis, list):
        add_error(errors, "apis_type", "apis", "apis must be an array.")
        return {"valid": False, "api_count": 0, "errors": errors}

    ids: set[str] = set()
    canonical_keys: set[tuple[str, str, str]] = set()
    for index, record in enumerate(apis):
        validate_record(record, index, errors, ids, canonical_keys)
    return {"valid": not errors, "api_count": len(apis), "errors": errors}


def main() -> int:
    """加载 Registry，输出机器可读报告，并用退出码守住构建边界。"""

    args = parse_args()
    registry_path = Path(args.registry).expanduser().resolve()
    try:
        data = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        result = {
            "valid": False,
            "api_count": 0,
            "errors": [{"code": "load_error", "path": str(registry_path), "message": str(error)}],
        }
    else:
        result = validate_registry(data)

    sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
