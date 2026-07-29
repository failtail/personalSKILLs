# 后续 Skill 收录要求

本仓库用于收录可复用的个人 Codex Skill。每次新增或更新 Skill 前，按本规范检查；目标是让仓库中的内容可读、可安装、可验证，且不带机器私有状态。

## 1. 收录范围

可以收录：

- 可跨项目复用的工作流、领域知识或工具使用规范。
- 有明确触发场景、输入、输出和边界的 Skill。
- Skill 必需的 `references/`、`scripts/`、`assets/` 和 `agents/openai.yaml`。

不要收录：

- Codex 的 `.system/` 内置 Skill。
- 插件缓存、`node_modules/`、构建产物、测试缓存和 IDE 配置。
- API key、token、Cookie、`.env`、私钥、机器用户名、绝对本机路径或私人业务数据。
- 只为某一次对话临时编写、没有可复用工作流的提示词。

## 2. 目录与分类

新 Skill 必须放在：

```text
skills/<category>/<skill-name>/
```

分类按 Skill 的主要目的选择，而不是按实现语言或单个框架选择：

| 分类 | 用途示例 |
| --- | --- |
| `learning` | 源码学习、文档讲解、知识整理、练习辅助 |
| `engineering` | 代码维护、测试、发布、重构、质量流程 |
| `productivity` | 个人工作流、笔记、任务整理、文件处理 |
| `design` | 设计协作、UI 审查、视觉资产工作流 |
| `research` | 调研、资料核验、来源整理 |

新增分类前，确认它不能合理归入已有分类；分类名称使用小写英文和连字符。

Skill 名称规则：

- 目录名与 `SKILL.md` frontmatter 的 `name` 必须一致。
- 只使用小写字母、数字和连字符。
- 选择动作或能力导向的名称，例如 `source-study`、`release-notes`。
- 不用具体仓库、个人项目或一次性任务命名，除非该 Skill 本身只服务于该明确领域。

## 3. Skill 内容要求

每个 Skill 至少包含：

```text
<skill-name>/
├── SKILL.md
└── agents/openai.yaml
```

`SKILL.md` 必须：

- 使用有效 YAML frontmatter，至少包含 `name` 和 `description`。
- 在 `description` 中同时写清“做什么”和“何时触发”，因为这是自动发现依据。
- 描述明确的工作流、边界、关键产物和验证方式。
- 保持简洁；将按需读取的长文档放入 `references/`。
- 不要求模型执行未被用户授权的联网、安装、删除、推送、发布或代码修改操作。
- 不伪造源码事实、文件路径、命令输出、测试结果或外部服务状态。

可选目录的使用原则：

| 目录 | 仅在以下情况加入 |
| --- | --- |
| `references/` | 有详细规则、模板、领域资料，需要按需读取 |
| `scripts/` | 存在重复且需要确定性执行的自动化步骤 |
| `assets/` | 输出需要复用模板、图片、字体或其他非文本资源 |

不要在 Skill 目录中添加 `README.md`、临时笔记、变更日志或重复的快速指南；仓库根 README 负责索引，`SKILL.md` 负责工作流。

## 4. 上传前检查

每次新增或修改 Skill，必须完成以下检查：

1. 确认目录放在正确分类下，名称与 frontmatter 一致。
2. 确认 `description` 能让 Codex 在正确场景触发，且不会无关泛触发。
3. 检查是否含有机密、绝对个人路径、依赖缓存或生成文件。
4. 使用官方校验器验证：

   ```powershell
   python E:\CodexData\skills\.system\skill-creator\scripts\quick_validate.py <skill-directory>
   ```

5. 至少用一个真实或接近真实的用户请求检查 Skill 的工作流是否能完成；复杂 Skill 优先做独立的前向测试。
6. 执行 Git whitespace 检查：

   ```powershell
   git diff --check
   ```

7. 更新仓库根 `README.md` 的“Included Skills”表格。

## 5. 本机安装副本与收录副本

个人 Codex Skills 实际安装目录与本仓库是两个位置：

```text
安装目录：E:\CodexData\skills\<skill-name>
收录目录：E:\CodexData\personalSKILLs\skills\<category>\<skill-name>
```

上传前确认两份 Skill 内容一致。建议先在安装目录迭代和验证，再将最终版本复制到收录目录；不要把收录目录中的未验证修改直接当作安装版本。

## 6. Git 提交与推送

每次收录保持提交聚焦。推荐提交格式：

```text
feat: add <skill-name> skill
feat: extend <skill-name> workflow
fix: correct <skill-name> trigger rules
docs: update skill catalog
chore: normalize skill metadata
```

推荐流程：

```powershell
git status --short
git add README.md CONTRIBUTING.md skills/<category>/<skill-name>
git diff --cached --check
git commit -m "feat: add <skill-name> skill"
git push
```

推送失败时，不要重写历史或删除本地提交。先保留本地提交，确认网络和远端状态后重试 `git push`。

## 7. 最终提交清单

- [ ] Skill 位于 `skills/<category>/<skill-name>/`
- [ ] `name`、目录名、调用名一致
- [ ] `description` 说明能力和触发条件
- [ ] `agents/openai.yaml` 与当前 Skill 内容一致
- [ ] 可选资源只包含实际需要的内容
- [ ] 没有机密、缓存、系统内置 Skill 或机器私有文件
- [ ] 官方校验器通过
- [ ] 至少完成一次真实场景验证
- [ ] `git diff --check` 无 whitespace 问题
- [ ] 根 `README.md` 已更新
- [ ] 提交与推送状态已确认
