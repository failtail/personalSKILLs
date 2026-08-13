#!/usr/bin/env python3
"""从结构化 ThingJS Contract 单向生成可漂移检查的 TypeScript 声明。"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from contract_signature_schema import (
    STRUCTURED_CONTRACT_SCHEMA_VERSION,
    has_structured_signature,
    type_to_typescript,
    validate_structured_signature,
)


VERIFIED_STATES = {"existence_verified", "behavior_verified"}
SUPPORTED_KINDS = {"constructor", "method", "property"}


def parse_args() -> argparse.Namespace:
    """解析 Contract、声明输出和可选 drift check 参数。"""

    parser = argparse.ArgumentParser(description="Generate TypeScript declarations from a ThingJS Contract.")
    parser.add_argument("--contract", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report")
    parser.add_argument("--check", action="store_true", help="Fail when output is absent or differs from generated content.")
    return parser.parse_args()


def read_json(path: str) -> dict[str, Any]:
    """读取对象根 JSON；声明生成不接受损坏或数组输入。"""

    resolved = Path(path).expanduser().resolve()
    value = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {resolved}")
    return value


def contract_hash(contract: dict[str, Any]) -> str:
    """对规范化 Contract 计算源哈希，写入声明头并阻断手工漂移。"""

    payload = json.dumps(contract, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def parameter_text(parameters: list[dict[str, Any]]) -> str:
    """生成参数列表；default 只作为 Contract 元数据，不伪装成声明语法。"""

    values: list[str] = []
    for parameter in parameters:
        type_text = type_to_typescript(parameter["type"])
        if parameter.get("rest"):
            type_text = type_text[:-2] if type_text.endswith("[]") else type_text
            values.append(f"...{parameter['name']}: {type_text}[]")
        else:
            optional = "?" if parameter.get("optional", False) else ""
            values.append(f"{parameter['name']}{optional}: {type_text}")
    return ", ".join(values)


def member_declarations(record: dict[str, Any], omissions: list[dict[str, str]]) -> list[str]:
    """生成一个 API record 的声明；任一 overload 失败则只省略该 overload。"""

    kind = record.get("kind")
    owner = record.get("owner")
    name = record.get("name")
    declarations: list[str] = []
    signatures = record.get("signatures")
    if not isinstance(signatures, list):
        omissions.append({"id": record.get("id", ""), "reason": "signatures_missing"})
        return []
    for index, signature in enumerate(signatures):
        signature_path = f"apis[{record.get('_index', '?')}].signatures[{index}]"
        if not has_structured_signature(signature):
            omissions.append({"id": record.get("id", ""), "reason": "legacy_text_signature"})
            continue
        errors = validate_structured_signature(signature, signature_path, kind)
        if errors:
            omissions.append({"id": record.get("id", ""), "reason": "invalid_structured_signature", "details": json.dumps(errors, ensure_ascii=False)})
            continue
        parameters = parameter_text(signature["parameters"])
        if kind == "constructor":
            declarations.append(f"constructor({parameters});")
            continue
        return_type = type_to_typescript(signature["return_type"])
        if signature.get("async") and not return_type.startswith("Promise<"):
            return_type = f"Promise<{return_type}>"
        if kind == "method":
            declarations.append(f"{name}({parameters}): {return_type};")
        elif kind == "property" and not signature["parameters"]:
            declarations.append(f"{name}: {return_type};")
        else:
            omissions.append({"id": record.get("id", ""), "reason": "property_parameters_unsupported"})
    return declarations


def add_to_tree(tree: dict[str, Any], owner: str, declarations: list[str]) -> None:
    """按 `THING` 下的 namespace 路径组织 class 成员。"""

    segments = owner.split(".")
    if not segments or segments[0] != "THING" or len(segments) < 2:
        raise ValueError("Only THING-owned declarations can be emitted.")
    node = tree
    for segment in segments[1:-1]:
        node = node["namespaces"].setdefault(segment, {"namespaces": {}, "classes": defaultdict(list)})
    node["classes"][segments[-1]].extend(declarations)


def render_tree(node: dict[str, Any], indent: str = "  ") -> list[str]:
    """递归输出 namespace/class；成员排序保证 generator 输出稳定。"""

    lines: list[str] = []
    for namespace, child in sorted(node["namespaces"].items()):
        lines.append(f"{indent}namespace {namespace} {{")
        lines.extend(render_tree(child, indent + "  "))
        lines.append(f"{indent}}}")
    for class_name, members in sorted(node["classes"].items()):
        lines.append(f"{indent}class {class_name} {{")
        for member in sorted(set(members)):
            lines.append(f"{indent}  {member}")
        lines.append(f"{indent}}}")
    return lines


def generate(contract: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """生成声明正文和审计报告；无结构化证据时输出空声明而非猜测。"""

    source_hash = contract_hash(contract)
    included: list[str] = []
    omissions: list[dict[str, str]] = []
    tree: dict[str, Any] = {"namespaces": {}, "classes": defaultdict(list)}
    schema_version = contract.get("schema_version")
    if schema_version != STRUCTURED_CONTRACT_SCHEMA_VERSION:
        omissions.append({"id": "<contract>", "reason": "legacy_contract_schema_requires_migration"})
    elif contract.get("signature_schema_version") != 1:
        omissions.append({"id": "<contract>", "reason": "signature_schema_version_missing"})

    for index, raw_record in enumerate(contract.get("apis", [])):
        if not isinstance(raw_record, dict):
            omissions.append({"id": f"apis[{index}]", "reason": "record_not_object"})
            continue
        record = dict(raw_record)
        record["_index"] = index
        record_id = record.get("id", f"apis[{index}]")
        if record.get("contract_state") not in VERIFIED_STATES:
            omissions.append({"id": record_id, "reason": "contract_state_not_verified"})
            continue
        if record.get("usage_state") == "blocked":
            omissions.append({"id": record_id, "reason": "usage_state_blocked"})
            continue
        if record.get("kind") not in SUPPORTED_KINDS:
            omissions.append({"id": record_id, "reason": "api_kind_not_supported"})
            continue
        try:
            declarations = member_declarations(record, omissions)
            if declarations:
                add_to_tree(tree, record["owner"], declarations)
                included.append(record_id)
        except (KeyError, TypeError, ValueError) as error:
            omissions.append({"id": record_id, "reason": "generation_error", "details": str(error)})

    lines = [
        "// Generated file. Do not edit; regenerate from the pinned Contract.",
        f"// contract_id: {contract.get('contract_id', '<missing>')}",
        f"// contract_sha256: {source_hash}",
        f"// contract_schema_version: {schema_version}",
        "// Runtime Surface proves existence only; this file never defines Contract truth.",
        "",
        "declare namespace THING {",
    ]
    body = render_tree(tree)
    lines.extend(body or ["  // No eligible structured signatures."])
    lines.extend(["}", ""])
    report = {
        "generator_version": 1,
        "contract_id": contract.get("contract_id"),
        "contract_sha256": source_hash,
        "generated_output_sha256": hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest(),
        "contract_schema_version": schema_version,
        "included": sorted(included),
        "omitted": omissions,
        "declaration_count": len(included),
    }
    return "\n".join(lines), report


def main() -> int:
    """写出声明或执行严格 drift check；check 模式不修改目标文件。"""

    args = parse_args()
    contract = read_json(args.contract)
    content, report = generate(contract)
    output = Path(args.output).expanduser().resolve()
    if args.report:
        report_path = Path(args.report).expanduser().resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.check:
        current = output.read_text(encoding="utf-8") if output.exists() else None
        if current != content:
            print(json.dumps({"valid": False, "code": "generated_output_drift", "report": report}, ensure_ascii=False, indent=2))
            return 1
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
    print(json.dumps({"valid": True, "check": args.check, "report": report}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
