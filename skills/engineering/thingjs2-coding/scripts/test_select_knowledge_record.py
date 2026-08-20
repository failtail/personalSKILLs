#!/usr/bin/env python3
"""单条知识 selector 的标准库回归测试。"""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


SCRIPT = Path(__file__).with_name("select_knowledge_record.py")


def write_json(path: Path, payload: Any) -> None:
    """只在测试临时目录写入输入索引，不让被测 selector 产生输出文件。"""

    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_fixture(root: Path) -> dict[str, Any]:
    """构造包含一个可选源和一个不可读取语义哨兵的最小 schema-3 输入。"""

    source_root = root / "corpus"
    source = source_root / "开发示例" / "scene.md"
    source.parent.mkdir(parents=True)
    content = b"scene-source"
    source.write_bytes(content)
    # selector 不应遍历或把该文件原文复制到成功输出中。
    (source_root / "other-corpus.md").write_text("不应被读取的其他 corpus 原文", encoding="utf-8")

    source_path = "开发示例/scene.md"
    digest = hashlib.sha256(content).hexdigest()
    manifest_record = {
        "path": source_path,
        "sha256": digest,
        "bytes": len(content),
        "domain": "scene",
        "primary_class": "example_recipe_candidate",
        "risk_flags": [],
        "official_api_fact": False,
    }
    ledger_record = {
        "source_ref": "sources/engineer-corpus/2026-08-11/raw/开发示例/scene.md",
        "source_path": source_path,
        "sha256": digest,
        "bytes": len(content),
        "domain": "scene",
        "primary_class": "example_recipe_candidate",
        "evidence_class": "example_recipe_candidate",
        "risk_flags": [],
        "semantic_status": "candidate",
        "semantic_reason_codes": ["engineer_example_only"],
        "next_evidence_gate": "绑定 Contract、前置条件并通过真实 Behavior Test",
        "direct_promotion_decision": "candidate",
        "materialization_plan": "ledger_only",
        "official_api_fact": False,
    }
    manifest_path = root / "manifest.json"
    ledger_path = root / "ledger.json"
    write_json(manifest_path, {"schema_version": 3, "records": [manifest_record]})
    write_json(ledger_path, {"schema_version": 3, "records": [ledger_record]})
    return {
        "source_root": source_root,
        "source": source,
        "manifest": manifest_path,
        "ledger": ledger_path,
        "source_path": source_path,
        "manifest_record": manifest_record,
        "ledger_record": ledger_record,
    }


def run_selector(fixture: dict[str, Any], *, source_file: Path | None = None) -> subprocess.CompletedProcess[str]:
    """以真实 CLI 进程运行 selector，验证 stdout/stderr 和退出码边界。"""

    command = [
        sys.executable,
        str(SCRIPT),
        "--source-root",
        str(fixture["source_root"]),
        "--source-file",
        str(source_file or fixture["source"]),
        "--manifest",
        str(fixture["manifest"]),
        "--ledger",
        str(fixture["ledger"]),
    ]
    return subprocess.run(command, capture_output=True, text=True, check=False)


class SelectKnowledgeRecordTests(unittest.TestCase):
    """验证精确选择和全部指定的 fail-closed 场景。"""

    def test_valid_outputs_only_compact_selection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = make_fixture(root)
            before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())
            result = run_selector(fixture)
            after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "")
            self.assertEqual(before, after)
            payload = json.loads(result.stdout)
            self.assertEqual(
                list(payload),
                ["valid", "source_path", "sha256", "manifest_record", "ledger_record"],
            )
            self.assertEqual(
                result.stdout,
                json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
            )
            self.assertIs(payload["valid"], True)
            self.assertEqual(payload["source_path"], fixture["source_path"])
            self.assertEqual(payload["manifest_record"], fixture["manifest_record"])
            self.assertEqual(payload["ledger_record"], fixture["ledger_record"])
            self.assertNotIn("不应被读取的其他 corpus 原文", result.stdout)

    def test_unindexed_source_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = make_fixture(root)
            write_json(fixture["manifest"], {"schema_version": 3, "records": []})
            write_json(fixture["ledger"], {"schema_version": 3, "records": []})
            result = run_selector(fixture)
            self.assert_blocked(result, "manifest_not_indexed")

    def test_source_outside_root_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = make_fixture(root)
            outside = root / "outside.md"
            outside.write_bytes(b"outside")
            result = run_selector(fixture, source_file=outside)
            self.assert_blocked(result, "source_outside_root")

    def test_source_hash_mismatch_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = make_fixture(root)
            fixture["source"].write_bytes(b"scene-drift?")
            result = run_selector(fixture)
            self.assert_blocked(result, "manifest_hash_mismatch")

    def test_duplicate_manifest_path_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = make_fixture(root)
            manifest = json.loads(fixture["manifest"].read_text(encoding="utf-8"))
            manifest["records"].append(copy.deepcopy(manifest["records"][0]))
            write_json(fixture["manifest"], manifest)
            result = run_selector(fixture)
            self.assert_blocked(result, "manifest_duplicate_path")

    def test_duplicate_ledger_path_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = make_fixture(root)
            ledger = json.loads(fixture["ledger"].read_text(encoding="utf-8"))
            ledger["records"].append(copy.deepcopy(ledger["records"][0]))
            write_json(fixture["ledger"], ledger)
            result = run_selector(fixture)
            self.assert_blocked(result, "ledger_duplicate_path")

    def test_ledger_missing_governance_field_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = make_fixture(root)
            ledger = json.loads(fixture["ledger"].read_text(encoding="utf-8"))
            del ledger["records"][0]["next_evidence_gate"]
            write_json(fixture["ledger"], ledger)
            result = run_selector(fixture)
            self.assert_blocked(result, "ledger_required_field")

    def test_official_fact_overreach_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = make_fixture(root)
            ledger = json.loads(fixture["ledger"].read_text(encoding="utf-8"))
            ledger["records"][0]["official_api_fact"] = True
            write_json(fixture["ledger"], ledger)
            result = run_selector(fixture)
            self.assert_blocked(result, "official_api_fact_forbidden")

    def test_manifest_and_ledger_conflict_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = make_fixture(root)
            ledger = json.loads(fixture["ledger"].read_text(encoding="utf-8"))
            ledger["records"][0]["domain"] = "earth"
            write_json(fixture["ledger"], ledger)
            result = run_selector(fixture)
            self.assert_blocked(result, "manifest_ledger_conflict")

    def test_schema_version_drift_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = make_fixture(root)
            manifest = json.loads(fixture["manifest"].read_text(encoding="utf-8"))
            manifest["schema_version"] = 2
            write_json(fixture["manifest"], manifest)
            result = run_selector(fixture)
            self.assert_blocked(result, "index_schema_error")

    @staticmethod
    def assert_blocked(result: subprocess.CompletedProcess[str], code: str) -> None:
        """所有拒绝场景都必须非零、无成功 JSON，并在 stderr 保留错误码。"""

        if result.returncode == 0:
            raise AssertionError(f"selector unexpectedly succeeded: {result.stdout}")
        if result.stdout:
            raise AssertionError(f"selector leaked stdout on failure: {result.stdout}")
        if code not in result.stderr:
            raise AssertionError(f"missing {code!r} in stderr: {result.stderr}")


if __name__ == "__main__":
    unittest.main()
