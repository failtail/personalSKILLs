# Usage Promotion Queue Implementation

## 本次改动 API 速查

| 名称 | 中文释义 |
| --- | --- |
| `build_queue` | 将生产 AST Usage 缺口聚合为待审 Contract 晋级队列。 |
| `runtime_evidence` | 从 descriptor Runtime Surface 读取成员存在性，不推导签名或行为。 |
| `official_evidence` | 汇总旧 API Cache 中的官方证据候选，不把候选自动升级为 Contract。 |
| `markdown_report` | 生成可人工审阅且能回溯到 Usage Entity 的 Markdown 队列。 |

## Requirement Mapping

- Master Plan B1：按 `kind|owner|member` 聚合生产可达、AST 已解析且不在 Contract 的 Usage Entity。
- 证据边界：Contract、Runtime Surface 与 API Cache 分开读取；Runtime Surface 只证明存在性，API Cache 只提供待审官方证据候选。
- 可追溯性：每个队列项保留 Usage ID、源码文件/行列、使用次数、调用次数和 Artifact Set。
- 风险排序：以异步/teardown、事件 ownership、动画晚到结果和场景状态写入为保守提示，排序不改变 Contract 状态。

## Design and Flow

1. 过滤 `production_reachable === true` 且 `resolution_status` 为 `resolved` 或 `resolved_inherited` 的 Usage Entity。
2. 使用现有 Contract/Runtime inheritance matching 判断是否已经被直接或继承 owner 覆盖。
3. 对缺口按 canonical key 聚合，计算 domain、usage/file/call 统计、Runtime existence、官方证据和 lifecycle risk。
4. 生成稳定排序的 JSON，并从同一 JSON 视图生成 Markdown；脚本不会写回 Contract 或修改项目源代码。

## Key Decisions

- Regex finding、非生产 token 和 unresolved usage 永远只进入排除统计，不成为晋级需求。
- `enum`/`event` 保留在队列 schema 的 kind 集合中；当前 descriptor Runtime Surface 无法单独证明这两类语义时，状态为 `unknown`。
- domain 与 lifecycle risk 是 triage 元数据，必须在正式 Contract/Behavior Test 审查时重新核对，不能当作官方 API 语义。
- 旧 Registry 只作为迁移/证据候选输入；即便存在 `official_verified` 标签，也只输出 `candidate`，不自动生成 Contract。

## Validation

- `python scripts/test_usage_promotion_queue.py`
- `python -m py_compile scripts/build_usage_promotion_queue.py scripts/test_usage_promotion_queue.py`
- 使用目标项目的 Usage Surface、2.0.13 Contract、Runtime Surface 和 API Cache 生成用户级 JSON/Markdown 队列。

## Known Limitations

- 该队列不替代官方来源核验、Contract builder 或独立 Runtime Behavior Test。
- 领域和风险采用保守启发式，后续若新增更精确的 Overlay 字段，应保持旧输出可解释并增加 schema 版本。
