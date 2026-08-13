# Structured Contract and Declaration Implementation

## 本次改动 API 速查

| 名称 | 中文释义 |
| --- | --- |
| `validate_structured_signature` | 校验参数、返回类型、async 与 lifecycle 证据是否完整。 |
| `generate` | 从已验证的结构化 Contract 生成声明文本和审计报告。 |
| `generate_contract_dts.py --check` | 比较确定性声明输出并阻断手工 drift。 |
| `build_contract` | 从受控 Registry/Artifact/Runtime 输入生成 schema 3 Contract。 |

## Requirement Mapping

- B2 结构化签名：schema 3 增加 `signature_schema_version: 1`，支持参数 optional/default、return type、async、lifecycle 和显式类型 descriptor。
- 单向 `.d.ts`：只有 `existence_verified`/`behavior_verified` 且签名完整的记录进入声明；生成结果带 Contract ID、Contract SHA、generator version 和 output SHA。
- 安全省略：schema 2、文本签名、blocked/documented、未解析类型和不支持的 kind 不生成声明，不用 `any` 伪装完成。
- Drift gate：`run_contract_ci.py --dts-output` 调用 generator `--check`；输出变化或目标文件缺失返回非零。

## Design and Flow

1. `contract_signature_schema.py` 递归验证显式类型 descriptor 和结构化签名。
2. `build_versioned_contract.py` 为新构建结果写入 schema 3 标识；旧 schema 2 仍可被 Validator 读取。
3. `generate_contract_dts.py` 规范化 Contract 后计算源 hash，按 `THING` owner 生成 namespace/class 声明，并输出 omission report。
4. CI 在 Contract/Usage 验证后可选执行 byte-level drift check；声明文件永远不回写 Contract。

## Key Decisions

- Runtime Surface 只能证明成员存在，不能提供参数或返回类型；因此 descriptor 不能参与类型猜测。
- schema 2 保持可读和可验证，但必须经过结构化证据迁移后才能产生声明。
- `any`、未解析 `unknown` 和缺失 return type 直接拒绝；空声明是证据不足时的安全结果。
- output hash 与 Contract hash 分开记录，防止只看头部元数据而漏掉声明正文篡改。

## Validation

- `python scripts/test_structured_contract.py`
- `python scripts/test_contract_pipeline.py --parser-root <parser-root> --node <node>`
- `python scripts/test_usage_promotion_queue.py`
- 真实项目 schema 3 migration：0 validator errors、10 stale warnings、0 declarations、10 explicit omissions。
- 真实项目 CI：declaration drift step passed；项目自身仍以有依据的 `EXPECTED_BLOCK` 返回。

## Known Limitations

- 当前项目没有结构化官方参数/返回类型，因此真实 `.d.ts` 为空；需要后续受控证据迁移，不应从工程师资料或运行时推导。
- Behavior verification 不由声明生成器完成；readiness、顺序、渲染、cleanup 和 failure 仍需 P4 独立 Behavior Test。
