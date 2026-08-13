#!/usr/bin/env python3
"""将生产可达的 AST Usage 缺口聚合为可追溯的 Contract 晋级队列。

该脚本只生成待审队列，不修改 Contract，也不把 Runtime Surface 或 Regex
发现升级为 API 事实。项目级输出应保存到用户级证据目录，而不是公共 Skill
仓库。
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from validate_contract import match_contract_record, runtime_index


QUEUE_SCHEMA_VERSION = 1
SUPPORTED_KINDS = {"constructor", "method", "property", "enum", "event"}
RESOLVED_STATES = {"resolved", "resolved_inherited"}
OFFICIAL_LABELS = {"official_verified", "official_unversioned"}
OFFICIAL_SOURCE_TYPES = {"official_api", "official_docs", "official_documentation"}


def parse_args() -> argparse.Namespace:
    """解析证据输入和两个独立输出路径。"""

    parser = argparse.ArgumentParser(
        description="Build a traceable ThingJS Usage Promotion Queue."
    )
    parser.add_argument("--usage-surface", required=True)
    parser.add_argument("--contract", required=True)
    parser.add_argument("--runtime-surface", required=True)
    parser.add_argument("--registry")
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-markdown", required=True)
    return parser.parse_args()


def read_json(path: str) -> dict[str, Any]:
    """读取对象根 JSON；输入错误必须显式失败，不能生成空队列。"""

    resolved = Path(path).expanduser().resolve()
    value = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {resolved}")
    return value


def canonical_parts(entity: dict[str, Any]) -> tuple[str, str, str] | None:
    """解析 kind|owner|member；缺少稳定身份的实体不能进入晋级队列。"""

    raw_key = entity.get("canonical_key")
    if not isinstance(raw_key, str):
        return None
    parts = tuple(raw_key.split("|", 2))
    if len(parts) != 3 or not all(parts):
        return None
    kind, owner, member = parts
    if kind not in SUPPORTED_KINDS:
        return None
    return kind, owner, member


def source_location(entity: dict[str, Any]) -> dict[str, Any]:
    """保留最小源码定位，供队列项回溯到 Usage Entity。"""

    source = entity.get("source")
    if not isinstance(source, dict):
        return {}
    return {
        key: source[key]
        for key in ("path", "line", "column", "block")
        if key in source
    }


def classify_domain(parts: tuple[str, str, str], entities: Iterable[dict[str, Any]]) -> str:
    """用 owner/member 和源码路径给候选分配检索域；这是排序元数据而非 API 事实。"""

    _kind, owner, member = parts
    owner_member = f"{owner.lower()} {member.lower()}"
    path_text = " ".join(
        str(entity.get("source", {}).get("path", "")).lower()
        for entity in entities
        if isinstance(entity.get("source"), dict)
    )

    def has_term(text: str, term: str) -> bool:
        """按词边界匹配目录或 owner，避免把 parking 误判为 park/campus。"""

        return re.search(rf"(?<![a-z]){re.escape(term)}(?![a-z])", text) is not None

    if "earth" in owner_member or has_term(path_text, "earth"):
        return "earth"
    if any(has_term(owner_member, term) for term in ("render", "style", "material", "shader", "light")):
        return "rendering"
    if any(has_term(owner_member, term) for term in ("camera", "viewpoint")):
        return "camera"
    if "eventtype" in owner_member or has_term(owner_member, "event") or member.lower() in {"on", "off"}:
        return "event"
    if any(term in owner_member for term in ("animation", "animate", "play", "move", "rotate")):
        return "animation"
    if any(has_term(owner_member, term) for term in ("query", "selector", "search")):
        return "query"
    if owner.lower().endswith(("app", "scene")) or member.lower() in {"load", "dispose"}:
        return "app_scene"
    if any(term in owner_member for term in ("entity", "object", "box", "label", "marker")):
        return "entity_lifecycle"
    if any(has_term(path_text, term) for term in ("campus", "building", "road")):
        return "campus"
    return "core"

def lifecycle_risk(
    parts: tuple[str, str, str],
    entities: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """计算可解释的排队风险；它提示验证工作量，不声称运行时行为已证实。"""

    _kind, owner, member = parts
    member_lower = member.lower()
    domain = classify_domain(parts, entities)
    signals: list[str] = []
    score = 0

    if member_lower in {"load", "waitforcomplete", "dispose", "destroy"}:
        signals.append("async_or_teardown_member")
        score += 3
    if member_lower in {"on", "off"}:
        signals.append("listener_ownership")
        score += 3
    if member_lower in {"playanimation", "pauseanimation", "moveto", "moveby"}:
        signals.append("animation_or_late_completion")
        score += 2
    if member_lower in {"position", "localposition", "rotation", "scale", "visible"}:
        signals.append("scene_state_or_rendering")
        score += 1
    if domain in {"app_scene", "event", "entity_lifecycle", "animation"}:
        signals.append(f"domain:{domain}")
        score += 1
    if any(entity.get("access_type") in {"construct", "call"} for entity in entities):
        signals.append("executable_access")
        score += 1

    if score >= 4:
        level = "high"
    elif score >= 2:
        level = "medium"
    else:
        level = "low"
    return {
        "level": level,
        "score": score,
        "signals": sorted(set(signals)),
        "requires_behavior_test": level == "high",
        "owner": owner,
    }


def runtime_evidence(
    parts: tuple[str, str, str],
    surface: dict[str, Any],
) -> dict[str, Any]:
    """读取 descriptor 证据；只返回成员存在性，不推导签名或生命周期。"""

    kind, owner, member = parts
    if kind not in {"constructor", "method", "property"}:
        return {
            "status": "unknown",
            "reason": f"Runtime Surface does not classify {kind} members.",
            "proves": "existence_only",
        }

    keys, inherited = runtime_index(surface)
    key = (kind, owner, member)
    if key in keys:
        return {"status": "present", "match": "direct_or_declared", "proves": "existence_only"}
    declared_owners = sorted(inherited.get(key, set()))
    if declared_owners:
        return {
            "status": "present",
            "match": "inherited",
            "declared_owners": declared_owners,
            "proves": "existence_only",
        }
    return {"status": "absent", "proves": "existence_only"}


def registry_index(registry: dict[str, Any] | None) -> dict[tuple[str, str, str], dict[str, Any]]:
    """以 canonical key 建立旧 API Cache 索引，保留它只是晋级候选输入。"""

    result: dict[tuple[str, str, str], dict[str, Any]] = {}
    for record in (registry or {}).get("apis", []):
        if not isinstance(record, dict):
            continue
        kind, owner, name = record.get("kind"), record.get("owner"), record.get("name")
        if all(isinstance(value, str) and value for value in (kind, owner, name)):
            result[(kind, owner, name)] = record
    return result


def official_evidence(record: dict[str, Any] | None) -> dict[str, Any]:
    """压缩 Registry 证据摘要；不存在官方证据时显式标记缺口。"""

    if record is None:
        return {"status": "missing", "labels": [], "source_refs": []}

    labels = sorted(str(label) for label in record.get("evidence_labels", []) if label)
    sources: list[dict[str, Any]] = []
    for source in record.get("sources", []):
        if not isinstance(source, dict):
            continue
        sources.append(
            {
                key: source[key]
                for key in (
                    "ref",
                    "source_id",
                    "source_type",
                    "retrieval_channel",
                    "url",
                    "version_relation",
                    "review_state",
                )
                if key in source
            }
        )
    is_official = bool(set(labels) & OFFICIAL_LABELS) or any(
        source.get("source_type") in OFFICIAL_SOURCE_TYPES for source in sources
    )
    blocked = record.get("usage_state") == "blocked" or record.get("project_status") == "runtime_conflict"
    status = "blocked" if blocked else "candidate" if is_official else "unverified"
    return {
        "status": status,
        "labels": labels,
        "source_refs": sources,
        "record_id": record.get("id"),
        "version_scope": record.get("version_scope"),
        "summary": record.get("summary"),
        "constraints": record.get("constraints", []),
        "lifecycle": record.get("lifecycle", []),
    }


def next_action(
    runtime: dict[str, Any],
    official: dict[str, Any],
    risk: dict[str, Any],
) -> str:
    """将证据缺口转换成顺序明确的人工动作，不生成自动晋级结论。"""

    if official["status"] == "blocked":
        return "保留冲突/阻断，先补充 Incident 或版本证据"
    if runtime["status"] == "absent":
        return "核对目标 Artifact Set，成员不存在则保持阻断"
    if runtime["status"] == "unknown":
        return "补充该 kind 的 Runtime Surface 证据边界"
    if official["status"] in {"missing", "unverified"}:
        return "补充受控官方 owner/signature 证据"
    if risk["requires_behavior_test"]:
        return "评审 Contract 候选并绑定独立 Behavior Test"
    return "评审 Contract 候选；仅存在性证据不足以声明行为"


def build_queue(
    usage: dict[str, Any],
    contract: dict[str, Any],
    surface: dict[str, Any],
    registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """聚合生产 Usage 缺口并按风险、影响面和证据缺口排序。"""

    contract_index = {
        (record.get("kind"), record.get("owner"), record.get("name")): record
        for record in contract.get("apis", [])
        if isinstance(record, dict)
    }
    _runtime_keys, inherited_owners = runtime_index(surface)
    cache_index = registry_index(registry)
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    excluded = Counter()

    for entity in usage.get("usage_entities", []):
        if not isinstance(entity, dict):
            excluded["invalid_entity"] += 1
            continue
        if entity.get("production_reachable") is not True:
            excluded["non_production"] += 1
            continue
        if entity.get("resolution_status") not in RESOLVED_STATES:
            excluded["unresolved"] += 1
            continue
        parts = canonical_parts(entity)
        if parts is None:
            excluded["non_canonical"] += 1
            continue
        record, _match_mode = match_contract_record(entity, contract_index, inherited_owners)
        if record is not None:
            excluded["already_in_contract"] += 1
            continue
        grouped[parts].append(entity)

    items: list[dict[str, Any]] = []
    risk_weights = {"high": 40, "medium": 20, "low": 5}
    evidence_weights = {"missing": 25, "unverified": 20, "candidate": 5, "blocked": 30}
    runtime_weights = {"absent": 20, "unknown": 15, "present": 0}

    for parts, entities in grouped.items():
        kind, owner, member = parts
        entities = sorted(
            entities,
            key=lambda entity: (
                str(entity.get("id", "")),
                str(entity.get("source", {}).get("path", "")),
                int(entity.get("source", {}).get("line", 0) or 0),
            ),
        )
        paths = sorted(
            {
                str(entity.get("source", {}).get("path"))
                for entity in entities
                if isinstance(entity.get("source"), dict) and entity.get("source", {}).get("path")
            }
        )
        usage_ids = sorted(str(entity.get("id")) for entity in entities if entity.get("id"))
        calls = sum(entity.get("access_type") in {"call", "construct"} for entity in entities)
        constructs = sum(entity.get("access_type") == "construct" for entity in entities)
        domain = classify_domain(parts, entities)
        risk = lifecycle_risk(parts, entities)
        runtime = runtime_evidence(parts, surface)
        official = official_evidence(cache_index.get(parts))
        priority_score = (
            risk_weights[risk["level"]]
            + evidence_weights[official["status"]]
            + runtime_weights[runtime["status"]]
            + min(len(entities), 100) * 2
            + min(len(paths), 20) * 5
            + min(calls, 50)
        )
        items.append(
            {
                "canonical_key": "|".join(parts),
                "kind": kind,
                "owner": owner,
                "member": member,
                "domain": domain,
                "production_usage_count": len(entities),
                "production_file_count": len(paths),
                "call_count": calls,
                "construct_count": constructs,
                "source_paths": paths,
                "usage_ids": usage_ids,
                "usage_locations": [source_location(entity) for entity in entities],
                "runtime_evidence": runtime,
                "official_evidence": official,
                "lifecycle_risk": risk,
                "priority_score": priority_score,
                "next_action": next_action(runtime, official, risk),
            }
        )

    items.sort(key=lambda item: (-item["priority_score"], item["canonical_key"]))
    for rank, item in enumerate(items, start=1):
        item["priority_rank"] = rank

    artifact_set_id = contract.get("sdk_binding", {}).get("artifact_set_id")
    return {
        "schema_version": QUEUE_SCHEMA_VERSION,
        "queue_type": "thingjs2_usage_promotion",
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "scope": {
            "production_reachable_only": True,
            "resolution_states": sorted(RESOLVED_STATES),
            "excluded_from_demand": ["regex_discovery", "non_production", "unresolved"],
            "contract_is_not_modified": True,
        },
        "contract": {
            "contract_id": contract.get("contract_id"),
            "sdk_version": contract.get("sdk_binding", {}).get("sdk_version"),
            "artifact_set_id": artifact_set_id,
        },
        "summary": {
            "candidate_count": len(items),
            "usage_entity_count": len(usage.get("usage_entities", [])),
            "regex_discovery_count": len(usage.get("discovery_findings", [])),
            "excluded": dict(sorted(excluded.items())),
            "by_kind": dict(sorted(Counter(item["kind"] for item in items).items())),
            "by_domain": dict(sorted(Counter(item["domain"] for item in items).items())),
            "by_risk": dict(sorted(Counter(item["lifecycle_risk"]["level"] for item in items).items())),
            "by_runtime_status": dict(
                sorted(Counter(item["runtime_evidence"]["status"] for item in items).items())
            ),
            "by_official_evidence": dict(
                sorted(Counter(item["official_evidence"]["status"] for item in items).items())
            ),
        },
        "items": items,
        "limitations": [
            "Priority is triage metadata; it does not promote a Contract record.",
            "Runtime Surface proves existence only and cannot supply signatures or behavior.",
            "Domain and lifecycle risk are conservative routing heuristics, not API semantics.",
            "Inherited Contract matching follows the current Runtime Surface inheritance graph.",
        ],
    }


def markdown_report(queue: dict[str, Any]) -> str:
    """生成适合人工审阅的队列表格和逐项回溯信息。"""

    summary = queue["summary"]
    contract = queue["contract"]
    lines = [
        "# ThingJS 2.0 Usage Promotion Queue",
        "",
        "本报告只列出生产可达且 AST 已解析、但尚未进入 pinned Contract 的 canonical API。",
        "Regex finding、非生产 token、dynamic/ambiguous usage 不会成为晋级需求；排序也不代表自动晋级。",
        "",
        f"- SDK：`{contract.get('sdk_version') or 'unknown'}`",
        f"- Contract：`{contract.get('contract_id') or 'unknown'}`",
        f"- Artifact Set：`{contract.get('artifact_set_id') or 'unknown'}`",
        f"- 候选数：`{summary['candidate_count']}`；Usage Entity：`{summary['usage_entity_count']}`；Regex finding：`{summary['regex_discovery_count']}`",
        "",
        "## 排序队列",
        "",
        "| Rank | Canonical API | Domain | Usage | Files | Calls | Runtime | Official evidence | Lifecycle risk | Next action |",
        "| ---: | --- | --- | ---: | ---: | ---: | --- | --- | --- | --- |",
    ]
    for item in queue["items"]:
        lines.append(
            "| {priority_rank} | `{canonical_key}` | {domain} | {production_usage_count} | "
            "{production_file_count} | {call_count} | {runtime} | {official} | {risk} | {action} |".format(
                priority_rank=item["priority_rank"],
                canonical_key=item["canonical_key"],
                domain=item["domain"],
                production_usage_count=item["production_usage_count"],
                production_file_count=item["production_file_count"],
                call_count=item["call_count"],
                runtime=item["runtime_evidence"]["status"],
                official=item["official_evidence"]["status"],
                risk=item["lifecycle_risk"]["level"],
                action=item["next_action"],
            )
        )
    lines.extend(["", "## 队列项回溯", ""])
    for item in queue["items"]:
        lines.extend(
            [
                f"### {item['priority_rank']}. `{item['canonical_key']}`",
                "",
                f"- Priority score：`{item['priority_score']}`；domain：`{item['domain']}`",
                f"- Usage IDs：{', '.join(f'`{value}`' for value in item['usage_ids'])}",
                f"- 源文件：{', '.join(f'`{value}`' for value in item['source_paths'])}",
                f"- Runtime：`{item['runtime_evidence']['status']}`；proves：`{item['runtime_evidence'].get('proves', 'n/a')}`",
                f"- Official evidence：`{item['official_evidence']['status']}`",
                f"- Lifecycle risk：`{item['lifecycle_risk']['level']}`（{', '.join(item['lifecycle_risk']['signals']) or 'none'}）",
                f"- 下一动作：{item['next_action']}",
                "- Usage locations：",
            ]
        )
        for location in item["usage_locations"]:
            lines.append(
                "  - "
                + ":".join(
                    str(location.get(key, "?"))
                    for key in ("path", "line", "column")
                )
            )
        lines.append("")
    lines.extend(
        [
            "## 边界",
            "",
            *[f"- {limitation}" for limitation in queue["limitations"]],
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    """构建 JSON/Markdown 两种视图并保证父目录存在。"""

    args = parse_args()
    queue = build_queue(
        read_json(args.usage_surface),
        read_json(args.contract),
        read_json(args.runtime_surface),
        read_json(args.registry) if args.registry else None,
    )
    json_path = Path(args.output_json).expanduser().resolve()
    markdown_path = Path(args.output_markdown).expanduser().resolve()
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(markdown_report(queue), encoding="utf-8")
    print(
        json.dumps(
            {
                "valid": True,
                "candidate_count": queue["summary"]["candidate_count"],
                "output_json": str(json_path),
                "output_markdown": str(markdown_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
