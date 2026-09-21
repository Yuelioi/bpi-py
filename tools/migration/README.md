# Rust 迁移清单工具

使用 Tree-sitter Rust AST 提取结构，JSON 契约提供协议证据。不是 Rust 编译器或代码翻译器。

## 输入与输出

从 Cargo `features.full` 取得领域集合；解析 `src/**/*.rs`，收集领域中的 `pub async fn` 声明以及 struct/enum/type 声明。显式 `cfg(test)` 和 tests 模块不进入结果。记录字段属性、参数绑定表达式、返回类型、WBI/认证方法调用、直接 HTTP 调用和控制流。

读取 `tests/contracts/**/contract.json`，保留请求、认证、cases、风险、步骤与 provenance，校验样例路径存在且在源根目录内。类型声明属于源库派生内容，保留 [MIT 归属](../../migration/SOURCE-LICENSE.txt)。

运行命令见[根 README](../../README.md)。输出目录必须在源仓库外，生成 `inventory.json` 和 `coverage.md`；只有成功解析全部输入后才开始输出。相同源提交、工作区状态和输入内容得到相同结果。输入哈希覆盖 Cargo、Rust、契约、关联样例以及 responses 下 JSON 文件；不记录本机绝对路径或生成时间。

`tracked_dirty` 仅表示 Git 跟踪文件状态；是否与本次扫描一致由输入哈希确定，不能仅凭 HEAD 判断。当前输出由 uv.lock 中 tree-sitter 0.25.2 / tree-sitter-rust 0.24.2 生成。

## 关联含义

| 状态 | 含义 |
| --- | --- |
| label_unique | 同一领域中仅一个公开异步声明在 send helper 中直接使用对应契约 ID |
| label_ambiguous | 多个声明直接使用同一契约 ID，需要人工选择 |
| url_candidate | 只发现 HTTP 方法与 URL 相同，参数/具体语义仍待核对 |
| flow_review | 多步骤流程契约，保留步骤，不当成单端点 |
| unmatched | 当前静态规则未能关联；不代表源码缺失 |

关联不依赖 API 索引中可能错误的函数名映射。常量只按同文件优先、同领域候选收集，不声称实现 Rust import/cfg/名称解析；相同 URL 多个入口仍保留候选关系。请求与契约不一致、同 ID 多方法等进入复核原因。

`request_shell_candidate` 仅意味着方法具有一个可识别直接请求、常规 payload helper、明确标签关联且未触发当前复核规则。它仍需检查参数辅助函数、字段转换、会话和协议。所有迁移状态当前为 `not_generated`，没有生成 SDK 业务代码。

## 明确局限

- 不展开宏、不求值 cfg、不追踪 re-export；声明数量不是编译后实际公开 API 数量。
- 第一波不展开跨函数调用；搜索 typed_search 和动态 URL 因此会进入复核列表。
- 收集领域异步声明，未盘点全部核心同步辅助方法的公共兼容性。
- 保留类型和 serde 属性，暂不转换模型或声称模型都可自动生成。
- 响应样例只校验路径和记录哈希，不在第一波验证其内容是否满足 Python 模型。
- 工具重跑覆盖自身生成报告；不会编辑人工维护的方案、源码或未来模型。

实现参考：[Python Tree-sitter](https://github.com/tree-sitter/py-tree-sitter)、[Rust grammar](https://github.com/tree-sitter/tree-sitter-rust)。
