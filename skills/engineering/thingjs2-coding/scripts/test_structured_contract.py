#!/usr/bin/env python3
"""回归测试 schema 3、结构化签名、单向 `.d.ts` 与 drift gate。"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from build_versioned_contract import build_contract
from contract_signature_schema import validate_structured_signature
from generate_contract_dts import generate
from validate_contract import validate_all


ARTIFACT_SHA = "a" * 64
ARTIFACT_SET_ID = "sha256:" + hashlib.sha256(
    f"core|thing.min.js|{ARTIFACT_SHA}".encode("utf-8")
).hexdigest()


def primitive(name: str) -> dict:
    """构造最小已解析 primitive 类型。"""

    return {"kind": "primitive", "name": name}


def source() -> dict:
    """使用 latest-only 官方 URL，验证 stale review 不影响结构化签名。"""

    return {
        "ref": "fixture-official",
        "source_type": "official_api",
        "url": "https://example.invalid/thingjs",
        "version_relation": "unversioned_latest",
    }


def record(kind: str, owner: str, name: str, signature: dict) -> dict:
    """构造带 Runtime existence 证据的 schema-3 API 记录。"""

    return {
        "id": f"fixture.{owner}.{name}",
        "kind": kind,
        "owner": owner,
        "name": name,
        "contract_state": "existence_verified",
        "usage_state": "allowed",
        "sources": [source()],
        "signatures": [signature],
        "existence_evidence": {
            "status": "supported",
            "artifact_set_id": ARTIFACT_SET_ID,
        },
    }


def signature(parameters: list[dict], return_type: dict | None, *, async_: bool = False) -> dict:
    """构造结构化签名；字段含义与 schema 1 保持显式。"""

    return {
        "text": "fixture controlled signature",
        "parameters": parameters,
        "return_type": return_type,
        "async": async_,
        "lifecycle": ["fixture ownership boundary"],
        "source_refs": ["fixture-official"],
    }


def contract() -> dict:
    """覆盖 App/Entity/BaseObject 的构造、方法、属性和 async。"""

    return {
        "schema_version": 3,
        "signature_schema_version": 1,
        "contract_id": "thingjs-fixture-schema3",
        "sdk_binding": {
            "sdk_version": "2.0.13",
            "artifact_set_id": ARTIFACT_SET_ID,
            "artifacts": [
                {"role": "core", "path": "thing.min.js", "sha256": ARTIFACT_SHA}
            ],
        },
        "apis": [
            record(
                "constructor",
                "THING.App",
                "constructor",
                signature(
                    [
                        {"name": "container", "type": primitive("string")},
                        {
                            "name": "debug",
                            "type": primitive("boolean"),
                            "optional": True,
                            "default": False,
                        },
                    ],
                    None,
                ),
            ),
            record(
                "constructor",
                "THING.Entity",
                "constructor",
                signature([{"name": "url", "type": primitive("string")}], None),
            ),
            record(
                "method",
                "THING.BaseObject",
                "destroy",
                signature([], primitive("boolean")),
            ),
            record(
                "method",
                "THING.BaseObject",
                "waitForComplete",
                signature([], {"kind": "reference", "name": "THING.Entity"}, async_=True),
            ),
            record(
                "property",
                "THING.BaseObject",
                "visible",
                signature([], primitive("boolean")),
            ),
        ],
    }


def surface() -> dict:
    """构造与 fixture Contract 对齐的 descriptor Surface。"""

    return {
        "schema_version": 1,
        "runtime_version": "2.0.13",
        "sdk_binding": {
            "sdk_version": "2.0.13",
            "artifact_set_id": ARTIFACT_SET_ID,
            "artifacts": [
                {"role": "core", "path": "thing.min.js", "sha256": ARTIFACT_SHA}
            ],
        },
        "constructors": [
            {"owner": "THING.App"},
            {"owner": "THING.Entity"},
        ],
        "namespace_members": [],
        "prototype_members": [
            {
                "effective_owner": "THING.BaseObject",
                "declared_owner": "THING.BaseObject",
                "member": "destroy",
                "kind": "method",
            },
            {
                "effective_owner": "THING.BaseObject",
                "declared_owner": "THING.BaseObject",
                "member": "waitForComplete",
                "kind": "method",
            },
            {
                "effective_owner": "THING.BaseObject",
                "declared_owner": "THING.BaseObject",
                "member": "visible",
                "kind": "property",
            },
        ],
        "inheritance": [{"child": "THING.Entity", "parent": "THING.BaseObject"}],
        "capture": {"mode": "browser_descriptor_probe", "page_errors": []},
    }


def builder_fixture() -> tuple[dict, dict, dict]:
    """构造 builder 输入，证明 legacy Registry 可输出 schema 3。"""

    registry = {"apis": [contract()["apis"][0]]}
    profile = {
        "sdk_artifacts": [
            {
                "path": "thing.min.js",
                "sha256": ARTIFACT_SHA,
                "version": "2.0.13",
            }
        ]
    }
    builder_surface = {
        "schema_version": 1,
        "sdk_binding": {"artifact_set_id": ARTIFACT_SET_ID},
        "constructors": [{"owner": "THING.App"}],
        "namespace_members": [],
        "prototype_members": [],
        "inheritance": [],
    }
    return registry, profile, builder_surface


def main() -> int:
    """执行结构校验、声明生成、漂移检测和 schema migration 断言。"""

    fixture_contract = contract()
    fixture_surface = surface()
    validation = validate_all(fixture_contract, fixture_surface, None, None)
    assert validation["valid"] is True, validation

    generated, report = generate(fixture_contract)
    assert report["declaration_count"] == 5
    assert len(report["generated_output_sha256"]) == 64
    assert "class App" in generated
    assert "constructor(container: string, debug?: boolean);" in generated
    assert "destroy(): boolean;" in generated
    assert "waitForComplete(): Promise<THING.Entity>;" in generated
    assert "visible: boolean;" in generated
    assert " any" not in generated
    assert " unknown" not in generated

    invalid = signature([], {"kind": "reference", "name": "unknown"})
    assert validate_structured_signature(invalid, "fixture", "method")

    legacy = {
        "schema_version": 2,
        "contract_id": "legacy",
        "sdk_binding": {"sdk_version": "2.0.13", "artifact_set_id": ARTIFACT_SET_ID},
        "apis": [
            {
                "id": "legacy.App",
                "kind": "constructor",
                "owner": "THING.App",
                "name": "constructor",
                "contract_state": "existence_verified",
                "usage_state": "allowed",
                "sources": [source()],
                "signatures": [{"text": "new THING.App(param)", "source_refs": ["fixture-official"]}],
                "existence_evidence": {"status": "supported", "artifact_set_id": ARTIFACT_SET_ID},
            }
        ],
    }
    legacy_output, legacy_report = generate(legacy)
    assert "No eligible structured signatures" in legacy_output
    assert any(item["reason"] == "legacy_contract_schema_requires_migration" for item in legacy_report["omitted"])

    with tempfile.TemporaryDirectory(prefix="thingjs-structured-contract-") as directory:
        root = Path(directory)
        contract_path = root / "contract.json"
        dts_path = root / "thingjs.generated.d.ts"
        report_path = root / "dts-report.json"
        contract_path.write_text(json.dumps(fixture_contract, ensure_ascii=False, indent=2), encoding="utf-8")
        generator = Path(__file__).resolve().parent / "generate_contract_dts.py"
        subprocess.run(
            [sys.executable, str(generator), "--contract", str(contract_path), "--output", str(dts_path), "--report", str(report_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        before = contract_path.read_bytes()
        subprocess.run(
            [sys.executable, str(generator), "--contract", str(contract_path), "--output", str(dts_path), "--check"],
            check=True,
            capture_output=True,
            text=True,
        )
        dts_path.write_text(dts_path.read_text(encoding="utf-8") + "// hand edit\n", encoding="utf-8")
        drift = subprocess.run(
            [sys.executable, str(generator), "--contract", str(contract_path), "--output", str(dts_path), "--check"],
            capture_output=True,
            text=True,
        )
        assert drift.returncode != 0
        assert contract_path.read_bytes() == before

    registry, profile, builder_surface = builder_fixture()
    built = build_contract(registry, profile, builder_surface)
    assert built["schema_version"] == 3
    assert built["signature_schema_version"] == 1
    assert built["apis"][0]["signatures"][0]["parameters"]

    print(json.dumps({"valid": True, "declaration_count": report["declaration_count"], "drift_gate": "passed"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
