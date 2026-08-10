# ThingJS 2.0 Skill 创建过程与阶段结果

这份记录说明 `thingjs2-coding` 为什么加入本仓库、如何验证，以及哪些材料明确不进入公共 Git 仓库。可执行的 Skill 位于 `skills/engineering/thingjs2-coding/`；运行时知识库和项目 Overlay 保留在使用者的 Codex 用户级工作区。

## V1 历史快照

本节保留首次实现的设计背景和验证边界。它不是当前运行时状态，也不应被
当作项目 SDK、浏览器连接或测试结果的永久事实。

- 复用本仓库，不新建仓库：本仓库已经定义了个人 Codex Skill 的目录、验证、索引和提交规范。
- 放入 `skills/engineering/`：ThingJS 2.0 Skill 的主要目的为实现、审查、调试和维护工作流。
- 公开 Skill 与项目知识分离：公共仓库只收录跨项目可复用的工作流、Schema、验证脚本和公开来源政策。
- 官方 ThingJS 2.0 来源是规范依据；内网资料只作为项目补充证据，不能进入公共 Skill。
- 不规定 Vue 或其他宿主框架；框架约定由目标项目自行提供。

## 实现阶段

1. **范围确认**：限定 ThingJS 2.x，排除 1.x、兼容/迁移接口、t3d 推测和未验证第三方 API。
2. **结构设计**：Skill 负责执行流程；用户级知识库负责 API 事实、示例、Recipe、Incident 和项目 Overlay。
3. **工具实现**：加入 SDK 指纹预检和 API 注册表校验脚本；脚本只读识别候选 `THING.*` 标识符，不把代码 token 自动升级为 API 真相。
4. **证据规则**：要求官方页面、精确签名、版本范围、生命周期边界和项目运行时冲突单独记录。
5. **真实任务验证**：使用当前 ThingJS 项目的代码、Git 历史、构建和测试结果建立基准；历史失败只记录为 Incident，不当作官方 API 证据。
6. **公共收录清理**：修正 `agents/openai.yaml` 的 UTF-8 编码；移除私有内网地址，改为项目配置项说明。

## 当前结果

- Skill 已形成可安装目录，包含 `SKILL.md`、`agents/openai.yaml`、按需读取的 `references/` 和可重复运行的 `scripts/`。
- 公开实现已提交到分支 `codex/add-thingjs2-coding-skill`，首个提交为 `feb37cd`（`feat: add thingjs2-coding skill`）；该分支已推送，尚未自动创建 PR。
- 首次实现建立了 SDK 预检、证据注册表校验和生命周期审计；目标项目的具体版本、路径、测试结果和浏览器状态均属于用户级工作区，不在这里维护。
- 首批 `THING.App`/场景加载、`THING.Entity`/完成回调、事件 `on/off`、对象 `destroy` 的网页取证曾被委派；未完成官方核验的条目不得升级为正式 API 事实。

## 公共仓库不包含的内容

- 内网 URL、内网 API 文本、登录状态、Cookie 和凭据；
- 具体项目的绝对路径、业务代码、私有 SDK 指纹和项目 Overlay；
- 未经官方网页核验的本地学习 Markdown；
- 构建缓存、测试缓存、依赖目录和机器配置。

## V2 Active Hybrid Policy

当前实现采用 `Minimal Skill + Context7 Retrieval + Official Web Fallback +
Lightweight Local Knowledge + Current Project Runtime`。详细职责和工程师资料
准入规则见 [`thingjs2-hybrid-policy.md`](thingjs2-hybrid-policy.md)。

工程师资料 ZIP 是高价值混合证据包，不是可直接导入的官方 API 库。其开发示例、
配方、FAQ 和园区/地球 API 文档必须分别分类为 Example、Recipe、Incident 或
API Cache candidate；明确的 1.x、兼容接口、私有字段、monkey-patch 和没有运行
证据的“已验证”声明不能进入 active 2.0 生成集合。`app.create` 等明确兼容路径
必须保持 blocked；`onComplete`/`complete`、`duration`/`time` 等冲突必须保留
为 overload 或 conflict，不能按参数表行号猜测。

V2 不再要求完整抓取公开网站、完整 API 镜像、大型 Canonical Registry 或大规模
Benchmark。保留 canonical identity、去重、来源追踪和 runtime conflict 能力，
但把注册表收敛为小型 API Cache；Smoke Test 收敛为 API Retrieval、Official
Example、Simple Business、Hallucination Trap、Local Knowledge 五题。

Context7 在没有真实可调用工具和查询结果时只能标记为未验证/不可用，不能宣称
已使用；官方网页和本地知识是 fallback。真实 Context7 状态、用户级 Local KB、
工程师 ZIP 原文、项目 Overlay、运行结果和 V1 原文归档均保留在用户级工作区，
不提交到公共仓库。

## 后续阶段

按 Git 阶段推进：先提交公共 Hybrid policy 与导航，再最小修改 Skill/source policy，
然后将 Canonical Registry 降级为 API Cache，最后定义五题 Smoke Test。每阶段都要
检查完整 diff、`git diff --check`、相关验证、聚焦提交和推送状态。只有满足公开来源、
精确签名、生命周期完整且无目标项目冲突的条目，才写入用户级知识库并作为下一次
公共 Skill 更新的候选。
