#!/usr/bin/env python3
"""生成 ThingJS 项目的只读运行时指纹与 API 候选清单。"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
SOURCE_SUFFIXES = {".js", ".mjs", ".cjs", ".ts", ".vue", ".html"}
SKIP_DIRECTORIES = {
    ".agents",
    ".codex",
    ".codex-logs",
    ".codex-ref",
    ".codex-ref-repos",
    ".git",
    ".idea",
    ".vscode",
    "build",
    "coverage",
    "dist",
    "node_modules",
}
MAX_SOURCE_BYTES = 2 * 1024 * 1024
THING_TOKEN_PATTERN = re.compile(r"\bTHING(?:\.[A-Za-z_$][\w$]*)+")
SDK_NAME_PATTERN = re.compile(r"^thing(?:\.[\w-]+)*(?:\.min)?\.js$", re.IGNORECASE)

# ThingJS 发布元数据在压缩文件中相邻导出；限定字段间距可避开第三方依赖里的 VERSION 常量。
RELEASE_METADATA_PATTERN = re.compile(
    r"\bVERSION\s*=\s*['\"](?P<version>\d+\.\d+\.\d+)['\"]"
    r".{0,512}?\bCOMPILETIME\s*=\s*['\"](?P<compile_time>[^'\"]+)['\"]"
    r".{0,512}?\bGITCOMMITHASH\s*=\s*['\"](?P<git_commit_hash>[^'\"]+)['\"]",
    re.DOTALL,
)


def parse_args() -> argparse.Namespace:
    """解析只读扫描范围和可选的用户级输出路径。"""

    parser = argparse.ArgumentParser(
        description="Fingerprint local ThingJS SDK artifacts and inventory explicit THING.* tokens."
    )
    parser.add_argument("--project-root", required=True, help="Target application repository root.")
    parser.add_argument(
        "--output",
        help="Optional JSON output path, normally under the user-level ThingJS 2.0 Overlay.",
    )
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    """流式计算制品 SHA-256，避免一次性加载大型 SDK 文件。"""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_release_metadata(data: bytes) -> dict[str, str] | None:
    """从 SDK 发布导出区读取版本、编译时间和上游提交。"""

    text = data.decode("utf-8", errors="ignore")
    match = RELEASE_METADATA_PATTERN.search(text)
    if not match:
        return None
    return match.groupdict()


def is_skipped(path: Path, root: Path) -> bool:
    """排除构建产物和依赖目录，避免把第三方代码计入项目 API 候选。"""

    try:
        relative_parts = path.relative_to(root).parts
    except ValueError:
        return True
    return any(part in SKIP_DIRECTORIES for part in relative_parts[:-1])


def discover_sdk_artifacts(root: Path) -> list[dict[str, Any]]:
    """发现本地 ThingJS JavaScript 制品并记录可复现指纹。"""

    artifacts: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.js")):
        if is_skipped(path, root) or not SDK_NAME_PATTERN.fullmatch(path.name):
            continue
        data = path.read_bytes()
        metadata = extract_release_metadata(data)
        version = metadata.get("version") if metadata else None
        artifacts.append(
            {
                "path": path.relative_to(root).as_posix(),
                "bytes": len(data),
                "sha256": sha256_file(path),
                "version": version,
                "version_scope": "2.x" if version and version.startswith("2.") else "unknown",
                "compile_time": metadata.get("compile_time") if metadata else None,
                "sdk_git_commit": metadata.get("git_commit_hash") if metadata else None,
            }
        )
    return artifacts


def inventory_thing_tokens(root: Path, sdk_paths: set[str]) -> dict[str, Any]:
    """列出显式 `THING.*` token；结果只是候选，不证明 API 存在。"""

    counts: Counter[str] = Counter()
    locations: dict[str, set[str]] = defaultdict(set)
    scanned_files = 0

    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        if is_skipped(path, root):
            continue
        # 压缩文件通常是 SDK 或外部插件，token 无法可靠归属到项目实现。
        if path.name.lower().endswith(".min.js"):
            continue
        relative = path.relative_to(root).as_posix()
        if relative in sdk_paths or path.stat().st_size > MAX_SOURCE_BYTES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        scanned_files += 1
        for token in THING_TOKEN_PATTERN.findall(text):
            counts[token] += 1
            locations[token].add(relative)

    tokens = [
        {
            "token": token,
            "occurrences": counts[token],
            "files": sorted(locations[token]),
        }
        for token in sorted(counts)
    ]
    return {
        "classification": "candidate_only",
        "scanned_files": scanned_files,
        "tokens": tokens,
    }


def read_git_state(root: Path) -> dict[str, Any] | None:
    """记录证据对应的仓库提交与脏状态，不修改 Git 工作区。"""

    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
    except (OSError, subprocess.CalledProcessError):
        return None
    return {"head": head, "dirty": bool(status), "changed_entries": len(status)}


def build_profile(root: Path) -> dict[str, Any]:
    """构造不会把候选 token 提升为 API 事实的项目 Profile。"""

    artifacts = discover_sdk_artifacts(root)
    sdk_paths = {artifact["path"] for artifact in artifacts}
    warnings: list[str] = []

    if not artifacts:
        warnings.append("No local ThingJS SDK artifact was discovered.")
    if artifacts and not any(artifact["version_scope"] == "2.x" for artifact in artifacts):
        warnings.append("No local artifact exposed a verified ThingJS 2.x release fingerprint.")

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "target_project_root": str(root),
        "git": read_git_state(root),
        "sdk_artifacts": artifacts,
        "thing_token_inventory": inventory_thing_tokens(root, sdk_paths),
        "warnings": warnings,
    }


def main() -> int:
    """执行扫描，并将相同 JSON 同步写入 stdout 与可选输出文件。"""

    args = parse_args()
    root = Path(args.project_root).expanduser().resolve()
    if not root.is_dir():
        print(json.dumps({"error": f"Project root is not a directory: {root}"}, ensure_ascii=False))
        return 2

    profile = build_profile(root)
    payload = json.dumps(profile, ensure_ascii=False, indent=2) + "\n"

    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")

    sys.stdout.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
