#!/usr/bin/env python3
"""在 CI 中生成当前 Profile/Usage Surface，并对版本化 Contract 执行发布门禁。"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


def issue_priority(code: str, severity: str) -> tuple[int, str]:
    """给 CI issue 分配修复顺序；warning 永远排在阻断错误之后。"""

    if severity == "warning":
        return 90, "复核非阻断漂移与发现项"
    if any(token in code for token in ("artifact", "schema", "runtime_capture", "incremental")):
        return 10, "先恢复证据身份、Schema 与完整 Surface"
    if code in {"blocked_api_usage", "behavior_evidence_missing", "failed_behavior_not_blocked"}:
        return 20, "处理已阻断 API 或缺失 Behavior 证据"
    if code in {"dynamic_usage_blocked", "production_parse_failure", "production_reachability_gap"}:
        return 30, "消除生产 unresolved、parse 或 reachability 缺口"
    if code == "usage_not_in_contract":
        return 40, "按 canonical API 补充受控 Contract 证据"
    return 50, "处理其余 Contract 发布门错误"


def _usage_entity_for_issue(
    issue: dict[str, Any],
    entities_by_id: dict[str, dict[str, Any]],
    entities: list[dict[str, Any]],
) -> dict[str, Any]:
    """Resolve an issue's Usage entity from either its stable id or validator array path."""

    by_id = entities_by_id.get(str(issue.get("usage_id")))
    if by_id:
        return by_id
    issue_path = str(issue.get("path", ""))
    prefix = "usage_entities["
    if issue_path.startswith(prefix) and issue_path.endswith("]"):
        index_text = issue_path[len(prefix) : -1]
        if index_text.isdigit() and int(index_text) < len(entities):
            return entities[int(index_text)]
    return {}


def build_developer_report(validation: dict[str, Any], usage_surface: dict[str, Any]) -> dict[str, Any]:
    """按错误类别、canonical API 与文件聚合 validator 结果，不改变原始证据。"""

    usage_entities = usage_surface.get("usage_entities", [])
    entities_by_id = {
        str(entity.get("id")): entity
        for entity in usage_entities
        if entity.get("id")
    }
    category_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    api_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    file_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for severity, collection in (("error", validation.get("errors", [])), ("warning", validation.get("warnings", []))):
        for issue in collection:
            code = str(issue.get("code", "unknown"))
            entity = _usage_entity_for_issue(issue, entities_by_id, usage_entities)
            source = issue.get("source") or entity.get("source", {})
            if isinstance(source, dict):
                source_path = str(source.get("path", ""))
            else:
                source_path = str(source)
            canonical_key = issue.get("canonical_key") or entity.get("canonical_key")
            if not canonical_key and entity:
                canonical_key = f"{entity.get('resolution_status', 'unresolved')}|{entity.get('id', 'unknown')}"
            priority, action = issue_priority(code, severity)
            normalized = {
                "severity": severity,
                "code": code,
                "priority": priority,
                "action": action,
                "canonical_key": canonical_key,
                "source_path": source_path or None,
                "usage_id": issue.get("usage_id"),
            }
            category_groups[(severity, code)].append(normalized)
            if canonical_key:
                api_groups[str(canonical_key)].append(normalized)
            if source_path:
                file_groups[source_path].append(normalized)

    def summarize_group(key: str, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "key": key,
            "count": len(items),
            "priority": min(item["priority"] for item in items),
            "codes": sorted({item["code"] for item in items}),
            "files": sorted({item["source_path"] for item in items if item.get("source_path")}),
            "canonical_keys": sorted({item["canonical_key"] for item in items if item.get("canonical_key")}),
        }

    categories = []
    for (severity, code), items in category_groups.items():
        group = summarize_group(code, items)
        group.update({"severity": severity, "action": items[0]["action"]})
        categories.append(group)
    categories.sort(key=lambda item: (item["priority"], item["severity"], -item["count"], item["key"]))
    apis = [summarize_group(key, items) for key, items in api_groups.items()]
    apis.sort(key=lambda item: (item["priority"], -item["count"], item["key"]))
    files = [summarize_group(key, items) for key, items in file_groups.items()]
    files.sort(key=lambda item: (item["priority"], -item["count"], item["key"]))
    return {
        "schema_version": 1,
        "report_type": "thingjs2_contract_ci_developer_report",
        "valid": validation.get("valid") is True,
        "summary": {
            "errors": len(validation.get("errors", [])),
            "warnings": len(validation.get("warnings", [])),
            "category_count": len(categories),
            "canonical_api_count": len(apis),
            "file_count": len(files),
        },
        "fix_order": categories,
        "by_canonical_api": apis,
        "by_file": files,
    }


def render_developer_report(report: dict[str, Any]) -> str:
    """渲染紧凑 Markdown；完整 issue 仍保留在原 validator JSON。"""

    summary = report["summary"]
    lines = [
        "# ThingJS Contract CI developer report",
        "",
        f"- Gate valid: `{str(report['valid']).lower()}`",
        f"- Errors: {summary['errors']}",
        f"- Warnings: {summary['warnings']}",
        "",
        "## Fix order",
        "",
        "| Priority | Severity | Code | Count | Action |",
        "| ---: | --- | --- | ---: | --- |",
    ]
    for item in report["fix_order"]:
        lines.append(f"| {item['priority']} | `{item['severity']}` | `{item['key']}` | {item['count']} | {item['action']} |")
    for title, key in (("Canonical APIs", "by_canonical_api"), ("Files", "by_file")):
        lines.extend(["", f"## {title}", "", "| Priority | Key | Count | Codes |", "| ---: | --- | ---: | --- |"])
        for item in report[key]:
            safe_key = str(item["key"]).replace("|", "\\|")
            lines.append(f"| {item['priority']} | `{safe_key}` | {item['count']} | {', '.join(item['codes'])} |")
    lines.extend(["", "> This report groups existing evidence only. It does not allowlist usage, promote Contract facts, or replace Runtime Behavior Tests.", ""])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    """解析可移植输入；所有生成文件写入调用方指定的证据目录。"""

    parser = argparse.ArgumentParser(description="Run the ThingJS Contract CI pipeline.")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--contract", required=True)
    parser.add_argument("--runtime-surface", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--parser-root")
    parser.add_argument("--entry", action="append", default=[])
    parser.add_argument("--allowlist")
    parser.add_argument("--alias-config", help="Optional JSON export of TypeScript/Vite path aliases.")
    parser.add_argument(
        "--usage-cache",
        help="Optional Usage resolver content-hash cache; complete surfaces only are cached.",
    )
    parser.add_argument(
        "--dts-output",
        help="Optional generated .d.ts path; when provided, --check detects declaration drift.",
    )
    parser.add_argument("--dts-report", help="Optional JSON report path for declaration generation.")
    parser.add_argument("--node", default="node")
    parser.add_argument("--python", default=sys.executable)
    return parser.parse_args()


def run(command: list[str], stdout_path: Path | None = None) -> int:
    """执行子步骤并保留原退出码；CI 不会把失败降级为告警。"""

    if stdout_path:
        with stdout_path.open("w", encoding="utf-8") as stream:
            completed = subprocess.run(command, text=True, stdout=stream, stderr=sys.stderr)
    else:
        completed = subprocess.run(command)
    return completed.returncode


def main() -> int:
    """串联 Preflight、AST Usage 和 Validator，并输出单一阶段摘要。"""

    args = parse_args()
    scripts = Path(__file__).resolve().parent
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    profile = output_dir / "project-profile.json"
    usage = output_dir / "usage-surface.json"
    report = output_dir / "contract-validation.json"

    steps = []
    preflight_code = run(
        [
            args.python,
            str(scripts / "preflight.py"),
            "--project-root",
            args.project_root,
            "--output",
            str(profile),
        ],
        output_dir / "preflight.stdout.json",
    )
    steps.append({"name": "preflight", "exit_code": preflight_code})
    if preflight_code != 0:
        print(json.dumps({"valid": False, "steps": steps}, ensure_ascii=False, indent=2))
        return preflight_code

    usage_command = [
        args.node,
        str(scripts / "extract_usage_surface.mjs"),
        "--project-root",
        args.project_root,
        "--parser-root",
        args.parser_root or args.project_root,
        "--output",
        str(usage),
        "--contract",
        args.contract,
    ]
    for entry in args.entry:
        usage_command.extend(["--entry", entry])
    if args.alias_config:
        usage_command.extend(["--alias-config", args.alias_config])
    if args.usage_cache:
        usage_command.extend(["--cache", args.usage_cache])
    usage_code = run(usage_command, output_dir / "usage.stdout.json")
    steps.append({"name": "usage_surface", "exit_code": usage_code})
    if usage_code != 0:
        print(json.dumps({"valid": False, "steps": steps}, ensure_ascii=False, indent=2))
        return usage_code

    validate_command = [
        args.python,
        str(scripts / "validate_contract.py"),
        "--contract",
        args.contract,
        "--runtime-surface",
        args.runtime_surface,
        "--usage-surface",
        str(usage),
        "--project-profile",
        str(profile),
        "--output",
        str(report),
    ]
    if args.allowlist:
        validate_command.extend(["--allowlist", args.allowlist])
    validate_code = run(validate_command, output_dir / "validator.stdout.json")
    steps.append({"name": "contract_validation", "exit_code": validate_code})

    validation_summary = {}
    developer_report_json = output_dir / "developer-report.json"
    developer_report_markdown = output_dir / "developer-report.md"
    if report.exists():
        validation_payload = json.loads(report.read_text(encoding="utf-8"))
        validation_summary = validation_payload.get("summary", {})
        usage_payload = json.loads(usage.read_text(encoding="utf-8"))
        developer_payload = build_developer_report(validation_payload, usage_payload)
        developer_report_json.write_text(
            json.dumps(developer_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        developer_report_markdown.write_text(render_developer_report(developer_payload), encoding="utf-8")
    declaration_code = 0
    declaration_report = None
    if args.dts_output:
        declaration_report = output_dir / "declaration-generation.json"
        declaration_command = [
            args.python,
            str(scripts / "generate_contract_dts.py"),
            "--contract",
            args.contract,
            "--output",
            args.dts_output,
            "--report",
            args.dts_report or str(declaration_report),
            "--check",
        ]
        declaration_code = run(declaration_command, output_dir / "declaration.stdout.json")
        steps.append({"name": "declaration_drift", "exit_code": declaration_code})
    print(
        json.dumps(
            {
                "valid": validate_code == 0 and declaration_code == 0,
                "steps": steps,
                "validation_summary": validation_summary,
                "artifacts": {
                    "project_profile": str(profile),
                    "usage_surface": str(usage),
                    "validation_report": str(report),
                    "developer_report_json": str(developer_report_json),
                    "developer_report_markdown": str(developer_report_markdown),
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return validate_code or declaration_code


if __name__ == "__main__":
    raise SystemExit(main())
