# Resolver v2 Implementation

Status: `IN_PROGRESS`
Tier: `L`
Updated: 2026-08-14

## Purpose

`extract_usage_surface.mjs` produces the AST-derived Project ThingJS Usage
Surface used by Contract validation. Resolver v2 adds a deliberately bounded
module-value pass. It improves traceability for ordinary ESM composition while
keeping uncertain values visible as `ambiguous`, `dynamic_unresolved`, or a
blocking reachability gap.

## Supported value flow

The resolver builds a static import graph and a module export table. Within the
supported boundary it can propagate:

- named imports and exports;
- default imports and default exports;
- namespace imports and namespace member access;
- explicit re-exports (`export { ... } from`) and star re-exports;
- constructor or instance references whose ThingJS owner is already proven by
  local AST evidence or a schema-3 structured Contract return type;
- configured aliases supplied as explicit JSON for `compilerOptions.paths`,
  `resolve.alias`, or `aliases`.

The resolver does not execute Vite/TypeScript configuration, infer types from
Runtime Surface member names, or treat an engineer example as a signature.

## Fixed-point and failure behavior

Export propagation runs for a fixed maximum of eight passes. The output records
`resolver.module_flow_converged`. A stable table sets this flag to `true`; a
cycle or propagation chain that still changes at the boundary sets it to
`false` and adds a production `cross_module_resolution_incomplete` gap. This is
fail-closed: the unresolved graph cannot become a verified ThingJS alias by
reaching the pass limit.

Conflicting exports merge to an ambiguous reference. Factory and callback
returns are not followed because the resolver cannot prove which value was
returned at a call site. Static `await import()` member use is also retained as
ambiguous. Dynamic constructor class maps remain unresolved. These cases are
intentional evidence boundaries, not parser errors.

普通跨模块工具函数不会仅因返回值成员访问而变成 Usage Entity。解析器只在导出函数的
静态 `return` 已能解析为 `THING` namespace、实例、实例成员、动态 ThingJS 路径或既有
ambiguous ThingJS 引用时，才把调用结果保留为 `ambiguous`。这会保留真实 ThingJS
factory 的审查门，同时避免数组、配置和业务对象的 `.map()`、`.length`、`.right` 等访问
污染 ThingJS Usage Surface。参数透传、回调返回和无法静态证明的分支仍不解析为
`resolved`。

## Review-only delta mode

`--changed-files <json>` validates the changed-file list, computes the reverse
static dependency closure, and emits entities from that closure. The extractor
still parses the full source inventory to build the module graph; it does not
yet provide content hashing, persisted symbol indexes, or cache invalidation.
Therefore the output marks:

```json
{
  "incremental": {
    "enabled": true,
    "complete_surface": false,
    "restriction": "Delta output is review metadata only; run a full extraction before Contract CI."
  }
}
```

`validate_contract.py` rejects this output with
`incremental_surface_incomplete`. A full extraction remains mandatory for a
Contract release. This distinction preserves correctness while leaving room
for a future hash/cache implementation.

`run_contract_ci.py --usage-cache <resolver-cache.json>` 会把同一缓存传递给 Usage extractor；
Contract validation 仍只接受最终 `complete_surface=true` 的完整结果。

## C02b 局部失效与缓存复用

缓存现在额外保存每个模块的 import graph、导出表、Usage Entity、parse failure、discovery
finding 和 reachability gap。内容 hash 或显式 changed file 产生失效种子后，resolver 沿
反向依赖图计算受影响闭包；只有闭包内模块重新解析和传播，其余模块复用缓存数据，最后
合并为新的完整 Usage Surface。配置指纹变化、缓存缺少模块索引或新增/删除模块时仍回到
完整提取，避免使用不完整缓存。

局部复用只优化静态模块边界，不改变 `ambiguous`、dynamic、parse failure 或 Contract
发布门禁；缓存输出会保留 `invalidated_files`、`analyzed_files` 和 `reused_files` 供审计。

## C02a 内容缓存

`--cache <resolver-cache.json>` 为完整 Usage Surface 保存源码内容 hash、Contract/alias/入口
配置指纹和上一次完整结果。内容与配置均未变化时，extractor 直接复用完整结果并报告
`cache.hit=true`；配置变化、文件新增/删除/修改或显式 `--changed-files` 会使缓存失效，
并回到完整提取。带显式 delta 的结果不会写入完整缓存，避免 review metadata 污染发布缓存。

这一切片已经是真实的 hash/config cache，但变化文件仍会触发完整提取；受影响模块及其
反向依赖的局部缓存复用留给 C02b。输出会报告 `invalidated_files` 和 `reused_files`，
不把缓存命中误报成目标项目兼容或行为验证。

## Deliberate non-goals

The current slice does not implement:

- cache reuse for an unchanged complete surface is implemented; changed-build cache reuse is
  limited to the affected-module/reverse-dependency slice described above;
- native Vite/TypeScript config execution or every alias plugin convention;
- general interprocedural call-graph analysis;
- dynamic constructor-to-class maps;
- runtime behavior or lifecycle verification.

The last item remains owned by the independent Behavior Test schema and real
browser runner. Resolver success never changes `behavior_verified`.

## Validation

The synthetic regression covers direct aliases, destructuring, structured
Contract nested owners, named/default/namespace imports, explicit and star
re-exports, conflicting exports, factory returns, static dynamic imports,
non-converged propagation, reverse-dependency delta output, and rejection of an
incomplete delta by Contract validation.

缓存回归还验证了首次写入、内容/配置指纹命中、完整 summary 复用和 delta 不写入完整
缓存；内容修改后只分析受影响闭包并复用其余模块，缓存命中不会改变 Usage Entity 数量
或解析状态。目标项目 Contract CI 通过 `run_contract_ci.py --usage-cache` 完成首跑和
命中复测，真实项目仍保持 `EXPECTED_BLOCK`。

The target ThingJS 2.0.13 project must be re-extracted after this slice. Its
existing release gate remains authoritative: improved resolution may reduce
ambiguity, but it cannot waive missing Contract entries, production unresolved
usage, Artifact Set mismatch, or missing behavior evidence.

## C01 结果

本轮将跨模块函数候选收窄到静态 `return` 可解析为 ThingJS 引用的函数。合成回归覆盖
函数声明、函数表达式、箭头函数、默认导出、re-export 和普通数组工具函数；真实项目
Usage 从 314 entities/103 ambiguous 恢复为 291 entities/80 ambiguous，resolved 保持
209，dynamic 保持 2，parse failure 保持 0。Contract CI 恢复为 233 errors/14 warnings，
`.d.ts` drift 通过。未知参数透传、回调返回和动态返回仍未升级为 `resolved`。
