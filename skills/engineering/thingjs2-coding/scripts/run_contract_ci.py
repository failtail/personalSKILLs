#!/usr/bin/env python3
"""在 CI 中生成当前 Profile/Usage Surface，并对版本化 Contract 执行发布门禁。"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


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
    ]
    for entry in args.entry:
        usage_command.extend(["--entry", entry])
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
    if report.exists():
        validation_summary = json.loads(report.read_text(encoding="utf-8")).get("summary", {})
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
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return validate_code or declaration_code


if __name__ == "__main__":
    raise SystemExit(main())
