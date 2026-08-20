#!/usr/bin/env python3
"""按源文件指纹从知识索引中选择唯一的工程师材料记录。

该工具只读取指定源文件、manifest 和 ledger，不扫描或复制同目录的其他
corpus 原文。任何路径越界、索引不唯一、指纹漂移或治理字段越权都会阻断
选择，避免把未经精确索引的材料送入后续知识流程。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import sys
from pathlib import Path, PurePosixPath
from typing import Any


EXPECTED_SCHEMA_VERSION = 3
SHA256_LENGTH = 64
SEMANTIC_STATUSES = {"candidate", "incident", "needs_review", "rejected"}
DIRECT_PROMOTION_DECISIONS = {"candidate", "incident", "rejected"}
MATERIALIZATION_PLANS = {
    "ledger_only",
    "phase_one_dossier",
    "curated_review_dossier",
}
REQUIRED_MANIFEST_FIELDS = ("path", "sha256", "bytes", "official_api_fact")
REQUIRED_LEDGER_FIELDS = (
    "source_path",
    "sha256",
    "bytes",
    "domain",
    "primary_class",
    "evidence_class",
    "risk_flags",
    "semantic_status",
    "semantic_reason_codes",
    "next_evidence_gate",
    "direct_promotion_decision",
    "materialization_plan",
    "official_api_fact",
)


class SelectorError(Exception):
    """携带稳定错误码的 fail-closed 选择失败。"""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def require(condition: bool, code: str, message: str) -> None:
    """把违反路径、指纹或治理不变量的情况统一转换为清晰阻断。"""

    if not condition:
        raise SelectorError(code, message)


def is_non_empty_string(value: Any) -> bool:
    """判断 JSON 字段是否为非空字符串。"""

    return isinstance(value, str) and bool(value.strip())


def is_normalized_posix_path(value: Any) -> bool:
    """只接受不含越界、反斜杠或冗余分隔符的相对 POSIX 路径。"""

    if not is_non_empty_string(value) or value in {".", ".."}:
        return False
    if value.startswith("/") or "\\" in value:
        return False
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return False
    return posixpath.normpath(value) == value and str(PurePosixPath(value)) == value


def validate_sha256(value: Any, field_path: str) -> str:
    """校验并返回规范化的小写 SHA-256，拒绝大小写或长度不确定的摘要。"""

    require(
        isinstance(value, str)
        and len(value) == SHA256_LENGTH
        and all(character in "0123456789abcdef" for character in value),
        "invalid_sha256",
        f"{field_path} 必须是 64 位小写十六进制 SHA-256",
    )
    return value


def validate_bytes(value: Any, field_path: str) -> int:
    """校验原始字节数；布尔值不能借助 int 子类关系冒充字节数。"""

    require(
        type(value) is int and value >= 0,
        "invalid_bytes",
        f"{field_path} 必须是非负整数",
    )
    return value


def load_index(path_value: str, label: str) -> list[dict[str, Any]]:
    """读取并校验一个 schema-3 索引，失败时不返回部分记录。"""

    path = Path(path_value).expanduser()
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise SelectorError("index_read_error", f"{label} 无法读取：{path}；{error}") from error
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as error:
        raise SelectorError(
            "index_json_error",
            f"{label} 不是有效 JSON：{path}；第 {error.lineno} 行第 {error.colno} 列",
        ) from error

    require(isinstance(payload, dict), "index_schema_error", f"{label} 根节点必须是 JSON 对象")
    require(
        payload.get("schema_version") == EXPECTED_SCHEMA_VERSION,
        "index_schema_error",
        f"{label}.schema_version 必须为 {EXPECTED_SCHEMA_VERSION}",
    )
    records = payload.get("records")
    require(isinstance(records, list), "index_schema_error", f"{label}.records 必须是数组")
    return records


def validate_manifest_records(records: list[dict[str, Any]]) -> None:
    """验证 manifest 的全量路径唯一性和源指纹字段。"""

    seen: set[str] = set()
    for index, record in enumerate(records):
        prefix = f"manifest.records[{index}]"
        require(isinstance(record, dict), "manifest_record_schema", f"{prefix} 必须是对象")
        missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in record]
        require(
            not missing,
            "manifest_required_field",
            f"{prefix} 缺少必需字段：{', '.join(missing)}",
        )
        source_path = record["path"]
        require(
            is_normalized_posix_path(source_path),
            "manifest_path_schema",
            f"{prefix}.path 必须是规范化相对 POSIX 路径",
        )
        require(
            source_path not in seen,
            "manifest_duplicate_path",
            f"manifest 按 path 重复：{source_path}",
        )
        seen.add(source_path)
        validate_sha256(record["sha256"], f"{prefix}.sha256")
        validate_bytes(record["bytes"], f"{prefix}.bytes")
        require(
            record["official_api_fact"] is False,
            "official_api_fact_forbidden",
            f"{prefix}.official_api_fact 必须为 false；工程师材料不能越权成为官方 API 事实",
        )


def validate_string_list(value: Any, field_path: str, *, allow_empty: bool) -> None:
    """校验风险标签或原因码数组，保留空风险数组但不接受非字符串元素。"""

    require(isinstance(value, list), "ledger_field_schema", f"{field_path} 必须是数组")
    if not allow_empty:
        require(bool(value), "ledger_required_field", f"{field_path} 不能为空")
    require(
        all(is_non_empty_string(item) for item in value),
        "ledger_field_schema",
        f"{field_path} 必须只包含非空字符串",
    )


def validate_ledger_records(records: list[dict[str, Any]]) -> None:
    """验证 ledger 的唯一性、治理字段和 fail-closed 晋级映射。"""

    seen: set[str] = set()
    for index, record in enumerate(records):
        prefix = f"ledger.records[{index}]"
        require(isinstance(record, dict), "ledger_record_schema", f"{prefix} 必须是对象")
        missing = [field for field in REQUIRED_LEDGER_FIELDS if field not in record]
        require(
            not missing,
            "ledger_required_field",
            f"{prefix} 缺少必需治理字段：{', '.join(missing)}",
        )

        source_path = record["source_path"]
        require(
            is_normalized_posix_path(source_path),
            "ledger_path_schema",
            f"{prefix}.source_path 必须是规范化相对 POSIX 路径",
        )
        require(
            source_path not in seen,
            "ledger_duplicate_path",
            f"ledger 按 source_path 重复：{source_path}",
        )
        seen.add(source_path)
        validate_sha256(record["sha256"], f"{prefix}.sha256")
        validate_bytes(record["bytes"], f"{prefix}.bytes")

        for field in ("domain", "primary_class", "evidence_class", "next_evidence_gate"):
            require(
                is_non_empty_string(record[field]),
                "ledger_required_field",
                f"{prefix}.{field} 必须是非空字符串",
            )
        validate_string_list(record["risk_flags"], f"{prefix}.risk_flags", allow_empty=True)
        validate_string_list(
            record["semantic_reason_codes"],
            f"{prefix}.semantic_reason_codes",
            allow_empty=False,
        )

        semantic_status = record["semantic_status"]
        require(
            semantic_status in SEMANTIC_STATUSES,
            "ledger_semantic_status",
            f"{prefix}.semantic_status 不受支持：{semantic_status!r}",
        )
        direct_decision = record["direct_promotion_decision"]
        require(
            direct_decision in DIRECT_PROMOTION_DECISIONS,
            "ledger_direct_decision",
            f"{prefix}.direct_promotion_decision 不受支持：{direct_decision!r}",
        )
        expected_decision = "rejected" if semantic_status in {"needs_review", "rejected"} else semantic_status
        require(
            direct_decision == expected_decision,
            "ledger_direct_decision_conflict",
            f"{prefix} 的 semantic_status={semantic_status!r} 与 direct_promotion_decision={direct_decision!r} 冲突",
        )
        require(
            record["materialization_plan"] in MATERIALIZATION_PLANS,
            "ledger_materialization_plan",
            f"{prefix}.materialization_plan 不受支持：{record['materialization_plan']!r}",
        )
        require(
            record["official_api_fact"] is False,
            "official_api_fact_forbidden",
            f"{prefix}.official_api_fact 必须为 false；ledger 不能晋级官方 API 事实",
        )


def resolve_source(source_root_value: str, source_file_value: str) -> tuple[Path, str, bytes, str]:
    """解析源文件并证明其真实路径位于 root 内，再读取该文件一次。"""

    try:
        source_root = Path(source_root_value).expanduser().resolve()
        source_file = Path(source_file_value).expanduser().resolve()
    except (OSError, RuntimeError) as error:
        raise SelectorError("source_path_error", f"源路径解析失败：{error}") from error
    require(source_root.is_dir(), "source_root_error", f"source-root 不是目录：{source_root}")
    require(source_file.is_file(), "source_file_error", f"source-file 不是文件：{source_file}")
    try:
        relative = source_file.relative_to(source_root)
    except ValueError as error:
        raise SelectorError(
            "source_outside_root",
            f"source-file 越出 source-root：{source_file} 不在 {source_root} 内",
        ) from error

    source_path = relative.as_posix()
    require(
        is_normalized_posix_path(source_path),
        "source_path_error",
        f"计算出的 source_path 不是规范化相对 POSIX 路径：{source_path}",
    )
    try:
        content = source_file.read_bytes()
    except OSError as error:
        raise SelectorError("source_read_error", f"source-file 无法读取：{source_file}；{error}") from error
    digest = hashlib.sha256(content).hexdigest()
    return source_file, source_path, content, digest


def select_record(
    source_root: str,
    source_file: str,
    manifest: str,
    ledger: str,
) -> dict[str, Any]:
    """执行单条选择并返回只含约定字段的结果对象。"""

    _, source_path, content, digest = resolve_source(source_root, source_file)
    source_bytes = len(content)

    manifest_records = load_index(manifest, "manifest")
    validate_manifest_records(manifest_records)
    ledger_records = load_index(ledger, "ledger")
    validate_ledger_records(ledger_records)

    manifest_matches = [record for record in manifest_records if record.get("path") == source_path]
    require(
        len(manifest_matches) == 1,
        "manifest_not_indexed",
        f"manifest 必须按 path 精确命中一条：{source_path}；实际命中 {len(manifest_matches)} 条",
    )
    ledger_matches = [record for record in ledger_records if record.get("source_path") == source_path]
    require(
        len(ledger_matches) == 1,
        "ledger_not_indexed",
        f"ledger 必须按 source_path 精确命中一条：{source_path}；实际命中 {len(ledger_matches)} 条",
    )
    manifest_record = manifest_matches[0]
    ledger_record = ledger_matches[0]

    require(
        manifest_record["bytes"] == source_bytes,
        "manifest_bytes_mismatch",
        f"manifest.bytes 与源文件不一致：期望 {source_bytes}，实际 {manifest_record['bytes']}",
    )
    require(
        manifest_record["sha256"] == digest,
        "manifest_hash_mismatch",
        f"manifest.sha256 与源文件不一致：期望 {digest}，实际 {manifest_record['sha256']}",
    )
    require(
        ledger_record["bytes"] == source_bytes,
        "ledger_bytes_mismatch",
        f"ledger.bytes 与源文件不一致：期望 {source_bytes}，实际 {ledger_record['bytes']}",
    )
    require(
        ledger_record["sha256"] == digest,
        "ledger_hash_mismatch",
        f"ledger.sha256 与源文件不一致：期望 {digest}，实际 {ledger_record['sha256']}",
    )

    shared_fields = {
        "path/source_path": (manifest_record["path"], ledger_record["source_path"]),
        "sha256": (manifest_record["sha256"], ledger_record["sha256"]),
        "bytes": (manifest_record["bytes"], ledger_record["bytes"]),
        "official_api_fact": (
            manifest_record["official_api_fact"],
            ledger_record["official_api_fact"],
        ),
    }
    for field, values in shared_fields.items():
        require(
            values[0] == values[1],
            "manifest_ledger_conflict",
            f"manifest 与 ledger 的 {field} 冲突：{values[0]!r} != {values[1]!r}",
        )

    for field in ("domain", "primary_class", "risk_flags"):
        if field in manifest_record and field in ledger_record:
            require(
                manifest_record[field] == ledger_record[field],
                "manifest_ledger_conflict",
                f"manifest 与 ledger 的 {field} 冲突：{manifest_record[field]!r} != {ledger_record[field]!r}",
            )

    return {
        "valid": True,
        "source_path": source_path,
        "sha256": digest,
        "manifest_record": manifest_record,
        "ledger_record": ledger_record,
    }


def parse_args() -> argparse.Namespace:
    """解析四个只读输入路径。"""

    parser = argparse.ArgumentParser(description="选择唯一且指纹一致的 ThingJS 工程师知识记录")
    parser.add_argument("--source-root", required=True, help="工程师 corpus 源文件根目录")
    parser.add_argument("--source-file", required=True, help="要选择的单个源文件")
    parser.add_argument("--manifest", required=True, help="schema-3 file manifest JSON")
    parser.add_argument("--ledger", required=True, help="schema-3 promotion ledger JSON")
    return parser.parse_args()


def main() -> int:
    """成功只向 stdout 输出 compact JSON；失败只向 stderr 输出阻断原因。"""

    args = parse_args()
    try:
        result = select_record(args.source_root, args.source_file, args.manifest, args.ledger)
    except SelectorError as error:
        print(f"selector error [{error.code}]: {error.message}", file=sys.stderr)
        return 1
    sys.stdout.write(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
