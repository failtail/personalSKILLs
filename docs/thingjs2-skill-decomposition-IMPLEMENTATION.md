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
| `select_knowledge_record.py` | 按源路径、字节数和 SHA-256 确定性选择一条 manifest/ledger 记录。 |
| `test_select_knowledge_record.py` | 锁定单条选择器的成功输出与 fail-closed 回归边界。 |

## C19 术语表

| 术语 | 含义 |
| --- | --- |
| `source_path` | source-file 在 source-root 内解析得到的规范化 POSIX 相对路径。 |
| `manifest_record` | 按 `path` 唯一命中且 bytes/SHA-256 与源文件一致的快照记录。 |
| `ledger_record` | 按 `source_path` 唯一命中并保留 domain、证据类别、风险、语义决定和 next gate 的治理记录。 |
| fail-closed | 路径、唯一性、指纹、schema 或治理不变量任一失败即非零停止，不返回可消费的成功 JSON。 |
| `Get-SkillTreeDigest` | 从 `SkillPath` 文件的父目录递归枚举非缓存文件，生成 `skill_tree_sha256`、严格文件计数和算法标识的 replay 完整性函数。 |
| strict count | `skill_tree_file_count` 必须是非负 JSON 整数 number；拒绝缺失、字符串、布尔值、小数和非有限数，并与枚举数量精确相等。 |
| `skill-tree-hash` target assertion | 负例先写入正确 tree 基线，再仅篡改摘要；验收必须出现专属 SHA mismatch，其他 complete-gate 失败不能代替该断言。 |

## Requirement Mapping

- **减少单文件臃肿**：保留稳定的 `coding-standards.md` 和转换索引，抽出 4 个有独立路由门的 child workflow；不按 API 数量拆文件。
- **保持渐进披露**：`SKILL.md` 仍只提供执行契约；`domain-routing.md` 先选 task mode，再按具体能力加载一个匹配 workflow。
- **保持证据门禁**：child workflow 只描述 ownership、顺序和清理；owner、signature、version、Contract、Runtime Surface 和 Behavior 仍由原有证据 references 与用户级 Overlay 决定。
- **补强转换契约**：在现有 `practice-workflows.md` 内定义 candidate/Recipe/Incident/rejected ledger 的最小字段，并在 R05 中固定 ledger-only、Recipe/Incident 晋级字段和 API/Contract 不变边界；不把工程师材料直接变成官方事实。
- **确定性单条选择**：C19 用只读标准库 CLI 将 source-root 内的一份源文件精确绑定到一条 manifest 和一条 ledger 记录；成功仅暴露单条 compact JSON，失败不提供可继续消费的部分结果。
- **Skill-tree replay 完整性**：C19 将公开/安装 Skill 的非缓存文件树绑定到结果记录的 SHA-256、严格计数和算法标识；缺失、漂移或算法变化都阻断 replay。

## Design and Flow

- **入口**：`SKILL.md` → `domain-routing.md` → `coding-standards.md` → 一个 matching child workflow。
- **知识转换**：`practice-workflows.md` 仅在 `convert`/`promote` 任务加载；工程师材料先分类，再绑定官方证据和项目 Behavior gate。
- **C19 选择流**：解析 source-root/source-file 的真实路径并证明边界 → 计算原始 bytes/SHA-256 → 校验 schema-3 manifest/ledger 的路径唯一性与治理字段 → 精确返回一组匹配记录；模型无需读取完整 ledger 或其他 corpus 原文。
- **C19 tree digest 流**：`Get-SkillTreeDigest` 要求 `SkillPath` 是文件，以其父目录为 root；递归结果先证明仍在 root 内，将相对路径统一为 `/`，按目录名和文件模式排除缓存/临时项，拒绝重复规范化路径，再用 `[StringComparer]::Ordinal` 排序。
- **精确摘要算法**：排除目录为 `__pycache__`、`node_modules`、`.git`、`.cache`、`.pytest_cache`、`.mypy_cache`、`.ruff_cache`、`coverage`、`dist`、`build`、`tmp`、`temp`；排除文件模式为 `*.pyc`、`*.pyo`、`*.log`、`*.tmp`、`*.temp`、`*.swp`、`*.swo`、`~*`、`*.bak`、`*.cache`、`npm-debug.log*`、`yarn-debug.log*`、`yarn-error.log*`、`.DS_Store`、`Thumbs.db`。每项追加 `relative_path + LF + uppercase content SHA-256 + LF`，整体以 UTF-8 no-BOM 编码后再做 SHA-256；算法标识必须精确等于 `thingjs-skill-tree-v1;sort=Ordinal;entry=relative-path+LF+uppercase-content-sha256+LF;manifest=UTF-8-no-BOM;digest=SHA-256;scope=non-cache-files`。
- **严格计数与记录比较**：计数只包含上述非缓存文件；结果记录必须同时提供 digest、count、algorithm。摘要按大写比较，algorithm 精确匹配，count 先通过非负 JSON 整数 number 类型门，再与枚举数量做精确数值比较。
- **失败边界**：缺少 owner/signature/version、生产 `ambiguous`/`dynamic_unresolved`、服务/认证不可用或缺少 Behavior evidence 时仍 fail-closed。
- **维护边界**：`gotchas.md`、Contract、evidence 和 project overlay 继续保持跨 workflow 的单一权威，不在 child workflow 中复制完整 API 清单。

## Key Decisions

- **保留两个基础文件**：实现门槛与知识转换索引职责不同，删除它们会把稳定规则重新复制到多个 child workflow。
- **拆成 4 个 child workflow**：每个文件对应 `domain-routing.md` 中已有的独立触发门；事件与实体生命周期分开，但都保留同一 owner/teardown 证据边界。
- **不创建第二套 `domains/` 目录**：当前公开证据不足以支持更多独立领域 bundle；未来只有当新领域有独立任务门和最小证据包时才增加文件。
- **不改变生成资格**：拆分只改变读取路径，不放宽 blocked Contract、生产 unresolved Usage、运行时认证或 Behavior promotion 规则。
- **C14 路由收窄**：未知成员的 `verify` 请求保持 `domain: null`；组合请求只记录一个 primary domain，场景替换等次级生命周期边界通过条件 child workflow 加载，避免把 domain 标签扩散成多域矩阵。
- **C18 体量决策**：本次只补强已有转换索引、评价规则和本实施文档；这是公共契约文字收敛，不新增目录、脚本或第二套 ledger。这样可保持 Skill 的渐进披露和文件规模，同时避免把低优先级或未过证据门的材料批量物化。
- **ledger-only 是合法结果**：未过证据门或低优先级记录保留最小机器字段和 next gate 即可；Recipe/Incident 真正晋级前才补齐 `preconditions`、`contract_ids`、`evidence_refs`，不得用 dossier 数量冒充知识完整度。
- **精确行复用**：已索引材料必须以 normalized path + SHA 精确命中并只读取一条 manifest/ledger 记录，原样保留其治理字段；未索引材料只能建立带 manifest/index gate 的 candidate，不能从文件名或原文重推 domain。
- **C19 两文件决策（L 级）**：选择器是跨 manifest、ledger 与源指纹的公共 fail-closed 契约，按 L 级记录设计与验证。保留一个运行脚本和一个独立测试文件是最小合理拆分：运行脚本把完整 ledger 的扫描与校验留在确定性进程内，只向模型返回单条 compact JSON；测试文件独立锁定越界、重复、漂移和越权阻断，避免把测试夹进运行时代码或要求模型加载全 ledger 自行判断。
- **完整性而非证据晋级**：Skill-tree digest 只证明 replay 使用的 Skill 输入未漂移；它不证明 activation、routing、output quality、Runtime Surface、Runtime Behavior、API Contract 或知识晋级，也不能把 synthetic/public-example 结果升级为真实目标运行证据。

## Validation

- Markdown 相对链接与路由路径检查通过，旧路径没有残留引用。
- C18 文档契约检查覆盖转换 ledger 最小字段、Recipe/Incident 晋级字段、ledger-only 输出边界，以及 R05 不改变 description、路由 `mode`/`domain` 和 API/Contract 状态的约束。
- C19 selector 的 10 项标准库回归、Sol 审查和真实 Earth 单条选择均已通过；覆盖 valid、未索引、路径越界、hash 漂移、manifest/ledger 重复、治理字段缺失、官方事实越权、索引冲突和 schema 漂移。
- C19 延期文档阶段复跑 Skill `quick_validate.py` 与 `git diff --check`；两者通过后才交付，且不修改 selector、测试或 evaluation 记录。
- **Standard replay**：无论是否 complete，结果记录都必须精确匹配当前非缓存 Skill tree 的 digest、strict count 和 algorithm；任一字段缺失或不匹配即失败。
- **Negative replay**：`skill-tree-hash` 场景必须产生非零阻断，并令 `target_assertion=true`，明确命中 `Recorded Skill tree SHA-256 does not match the enumerated non-cache Skill tree.`；其他失败不能冒充目标断言。
- **Complete replay**：在相同 tree 完整性门之上，仍要求 output coverage/quality 为 `PASS` 且目标项目 Runtime Behavior 为 `PASS`；tree 通过本身不能满足 complete gate。
- `SKILL.md` frontmatter 有效，description 1002 字符，仍在 1024 字符限制内。
- 现有 synthetic Contract/Usage/Behavior schema/queue 回归继续通过；真实项目的既有 `EXPECTED_BLOCK` 不被隐藏。
- 安装副本与公共 Skill 逐文件 SHA-256 一致；缓存目录不计入交付文件数。
- 已知限制：目标项目服务/认证仍不能提供真实 Behavior，Earth Artifact 与目标 CI 授权仍未提供；本次拆分不宣称总体 `COMPLETE`。
