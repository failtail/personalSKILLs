#!/usr/bin/env python3
"""定义 ThingJS Contract 的结构化签名和安全 TypeScript 类型表达式。"""

from __future__ import annotations

import re
from typing import Any


STRUCTURED_SIGNATURE_SCHEMA_VERSION = 1
STRUCTURED_CONTRACT_SCHEMA_VERSION = 3
PRIMITIVE_TYPES = {
    "bigint",
    "boolean",
    "false",
    "never",
    "null",
    "number",
    "string",
    "symbol",
    "true",
    "undefined",
    "void",
}
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*$")
SIMPLE_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")


def issue(path: str, message: str) -> dict[str, str]:
    """返回可嵌入 Contract validator/generator 报告的稳定错误。"""

    return {"path": path, "message": message}


def is_identifier(value: Any) -> bool:
    """限制生成到声明安全的标识符或点分 qualified name。"""

    return isinstance(value, str) and bool(IDENTIFIER_PATTERN.fullmatch(value))


def is_simple_identifier(value: Any) -> bool:
    """校验会直接出现在参数或对象属性位置的单段标识符。"""

    return isinstance(value, str) and bool(SIMPLE_IDENTIFIER_PATTERN.fullmatch(value))


def validate_type_descriptor(value: Any, path: str) -> list[dict[str, str]]:
    """递归校验结构化类型；拒绝 any/unknown，避免用伪类型掩盖证据缺失。"""

    errors: list[dict[str, str]] = []
    if not isinstance(value, dict):
        return [issue(path, "Structured type must be an object.")]
    kind = value.get("kind")
    if kind == "primitive":
        name = value.get("name")
        if name not in PRIMITIVE_TYPES:
            errors.append(issue(f"{path}.name", "Unsupported or unresolved primitive type."))
    elif kind == "reference":
        name = value.get("name")
        if not is_identifier(name) or name in {"any", "unknown"}:
            errors.append(issue(f"{path}.name", "Reference type must be a resolved qualified name."))
    elif kind in {"array", "promise"}:
        child = value.get("items") if kind == "array" else value.get("value")
        errors.extend(validate_type_descriptor(child, f"{path}.{'items' if kind == 'array' else 'value'}"))
    elif kind == "union":
        members = value.get("members")
        if not isinstance(members, list) or len(members) < 2:
            errors.append(issue(f"{path}.members", "Union type requires at least two members."))
        else:
            for index, member in enumerate(members):
                errors.extend(validate_type_descriptor(member, f"{path}.members[{index}]"))
    elif kind == "literal":
        literal = value.get("value")
        if not isinstance(literal, (str, int, float, bool)) or isinstance(literal, bool) and literal not in {True, False}:
            errors.append(issue(f"{path}.value", "Literal type requires a JSON scalar."))
    elif kind == "object":
        properties = value.get("properties")
        if not isinstance(properties, list):
            errors.append(issue(f"{path}.properties", "Object type requires a properties array."))
        else:
            for index, prop in enumerate(properties):
                prop_path = f"{path}.properties[{index}]"
                if not isinstance(prop, dict) or not is_simple_identifier(prop.get("name")):
                    errors.append(issue(prop_path, "Object property requires a valid name."))
                    continue
                errors.extend(validate_type_descriptor(prop.get("type"), f"{prop_path}.type"))
                if "optional" in prop and not isinstance(prop["optional"], bool):
                    errors.append(issue(f"{prop_path}.optional", "Optional must be boolean."))
    else:
        errors.append(issue(f"{path}.kind", "Unknown or unresolved structured type kind."))
    return errors


def validate_structured_signature(
    signature: Any,
    path: str,
    api_kind: str,
) -> list[dict[str, str]]:
    """校验单个签名的参数、返回类型、async 和 lifecycle 字段。"""

    if not isinstance(signature, dict):
        return [issue(path, "Signature must be an object.")]
    errors: list[dict[str, str]] = []
    parameters = signature.get("parameters")
    if not isinstance(parameters, list):
        errors.append(issue(f"{path}.parameters", "Structured signature requires a parameters array."))
    else:
        seen: set[str] = set()
        optional_seen = False
        for index, parameter in enumerate(parameters):
            parameter_path = f"{path}.parameters[{index}]"
            if not isinstance(parameter, dict) or not is_simple_identifier(parameter.get("name")):
                errors.append(issue(parameter_path, "Parameter requires a valid name."))
                continue
            name = parameter["name"]
            if name in seen:
                errors.append(issue(parameter_path, "Parameter names must be unique."))
            seen.add(name)
            errors.extend(validate_type_descriptor(parameter.get("type"), f"{parameter_path}.type"))
            optional = parameter.get("optional", False)
            if not isinstance(optional, bool):
                errors.append(issue(f"{parameter_path}.optional", "Optional must be boolean."))
            if parameter.get("default") is not None and optional is not True:
                errors.append(issue(f"{parameter_path}.default", "A default value requires optional=true."))
            if optional:
                optional_seen = True
            elif optional_seen:
                errors.append(issue(parameter_path, "Required parameters cannot follow optional parameters."))
            if parameter.get("rest", False) is True and index != len(parameters) - 1:
                errors.append(issue(parameter_path, "A rest parameter must be last."))
    return_type = signature.get("return_type")
    if api_kind == "constructor":
        if return_type is not None:
            errors.extend(validate_type_descriptor(return_type, f"{path}.return_type"))
    elif return_type is None:
        errors.append(issue(f"{path}.return_type", "Methods and properties require a resolved return_type."))
    else:
        errors.extend(validate_type_descriptor(return_type, f"{path}.return_type"))
    if "async" in signature and not isinstance(signature["async"], bool):
        errors.append(issue(f"{path}.async", "Async must be boolean."))
    lifecycle = signature.get("lifecycle", [])
    if not isinstance(lifecycle, list) or not all(isinstance(item, str) and item.strip() for item in lifecycle):
        errors.append(issue(f"{path}.lifecycle", "Lifecycle must be a list of non-empty strings."))
    return errors


def has_structured_signature(signature: Any) -> bool:
    """判断签名是否声明了结构化字段；纯 text signature 保持 legacy。"""

    return isinstance(signature, dict) and any(
        key in signature for key in ("parameters", "return_type", "async", "lifecycle")
    )


def type_to_typescript(value: dict[str, Any]) -> str:
    """将已校验的结构化类型转换为 TypeScript，不为失败类型提供兜底 any。"""

    errors = validate_type_descriptor(value, "type")
    if errors:
        raise ValueError(errors[0]["message"])
    kind = value["kind"]
    if kind == "primitive":
        return value["name"]
    if kind == "reference":
        return value["name"]
    if kind == "array":
        item = type_to_typescript(value["items"])
        return f"({item})[]" if " | " in item else f"{item}[]"
    if kind == "promise":
        return f"Promise<{type_to_typescript(value['value'])}>"
    if kind == "union":
        return " | ".join(type_to_typescript(member) for member in value["members"])
    if kind == "literal":
        literal = value["value"]
        return json_scalar_to_typescript(literal)
    properties = []
    for prop in value["properties"]:
        optional = "?" if prop.get("optional", False) else ""
        properties.append(f"{prop['name']}{optional}: {type_to_typescript(prop['type'])};")
    return "{ " + " ".join(properties) + " }"


def json_scalar_to_typescript(value: str | int | float | bool) -> str:
    """把 literal 标量安全地写成 TypeScript literal。"""

    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace("'", "\\'")
        return f"'{escaped}'"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)
