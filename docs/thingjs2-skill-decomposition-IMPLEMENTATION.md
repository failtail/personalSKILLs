# ThingJS 2.0 Skill decomposition implementation

## 本次改动 API 速查

| 名称 | 中文释义 |
| --- | --- |
| `coding-standards.md` | 实现、审查与最终 ThingJS Surface 审计的稳定门槛。 |
| `practice-workflows.md` | 工程师材料转换索引与 Example/Recipe/Incident 晋级边界。 |
| `workflows/scene-loading.md` | App 启动、场景加载、替换、取消和迟到结果清理。 |
| `workflows/entity-lifecycle.md` | Entity readiness、destroy、事件解绑与 teardown。 |
| `workflows/event-ownership.md` | 事件 owner、tag、重复监听和卸载规则。 |
| `workflows/camera-animation.md` | 相机/动画 readiness、ownership、时间字段冲突与单位边界。 |

## Requirement Mapping

- **减少单文件臃肿**：保留稳定的 `coding-standards.md` 和转换索引，抽出 4 个有独立路由门的 child workflow；不按 API 数量拆文件。
- **保持渐进披露**：`SKILL.md` 仍只提供执行契约；`domain-routing.md` 先选 task mode，再按具体能力加载一个匹配 workflow。
- **保持证据门禁**：child workflow 只描述 ownership、顺序和清理；owner、signature、version、Contract、Runtime Surface 和 Behavior 仍由原有证据 references 与用户级 Overlay 决定。

## Design and Flow

- **入口**：`SKILL.md` → `domain-routing.md` → `coding-standards.md` → 一个 matching child workflow。
- **知识转换**：`practice-workflows.md` 仅在 `convert`/`promote` 任务加载；工程师材料先分类，再绑定官方证据和项目 Behavior gate。
- **失败边界**：缺少 owner/signature/version、生产 `ambiguous`/`dynamic_unresolved`、服务/认证不可用或缺少 Behavior evidence 时仍 fail-closed。
- **维护边界**：`gotchas.md`、Contract、evidence 和 project overlay 继续保持跨 workflow 的单一权威，不在 child workflow 中复制完整 API 清单。

## Key Decisions

- **保留两个基础文件**：实现门槛与知识转换索引职责不同，删除它们会把稳定规则重新复制到多个 child workflow。
- **拆成 4 个 child workflow**：每个文件对应 `domain-routing.md` 中已有的独立触发门；事件与实体生命周期分开，但都保留同一 owner/teardown 证据边界。
- **不创建第二套 `domains/` 目录**：当前公开证据不足以支持更多独立领域 bundle；未来只有当新领域有独立任务门和最小证据包时才增加文件。
- **不改变生成资格**：拆分只改变读取路径，不放宽 blocked Contract、生产 unresolved Usage、运行时认证或 Behavior promotion 规则。
- **C14 路由收窄**：未知成员的 `verify` 请求保持 `domain: null`；组合请求只记录一个 primary domain，场景替换等次级生命周期边界通过条件 child workflow 加载，避免把 domain 标签扩散成多域矩阵。

## Validation

- Markdown 相对链接与路由路径检查通过，旧路径没有残留引用。
- `SKILL.md` frontmatter 有效，description 1002 字符，仍在 1024 字符限制内。
- 现有 synthetic Contract/Usage/Behavior schema/queue 回归继续通过；真实项目的既有 `EXPECTED_BLOCK` 不被隐藏。
- 安装副本与公共 Skill 逐文件 SHA-256 一致；缓存目录不计入交付文件数。
- 已知限制：目标项目服务/认证仍不能提供真实 Behavior，Earth Artifact 与目标 CI 授权仍未提供；本次拆分不宣称总体 `COMPLETE`。
