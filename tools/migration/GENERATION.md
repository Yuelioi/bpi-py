# 读取接口生成规则

`migration/batch-*.json` 是人工复核的参数和类型来源配置，后续按模块组织（例如 batch-video.json），旧批次保留以避免无关改动。`migration/generated/inventory.json` 提供 Rust AST 与契约证据。生成器合并配置后生成普通可读 Python；运行时无需清单或生成工具。不同源提交或冲突的模型配置会被拒绝。

```powershell
uv run python -m tools.migration.generate
uv run python -m tools.migration.generate --check
```

生成器只写 `src/bpi/_generated/{video,login,bangumi,audio,cheese,user}_{client,models}.py` 和 `migration/generated/batch-3.json`。写入前检查全部目标，拒绝覆盖没有生成标记的 Python 文件；`--check` 只比对，不写文件。Ruff 的锁定版本保证格式可重复。手写客户端通过继承导入生成方法，核心文件不由生成器编辑。

`migration/generated/batch-3.json` 为兼容上一批测试入口保留文件名，内容现在是合并后的生成清单；每个测试 recipe 的 batch 标识来源批次。源码生成标记升级时只接受已知旧标记，不放宽手写文件保护。

## 自动处理

- 契约 ID 对应的唯一常规 GET 方法；已复核 host 支持 api/www/api.vc/api.live，并要求配置与契约完全一致，可选 WBI。
- 默认必需 JSON payload；optional_payload=true 必须与源码的可空 helper 和 Option 返回类型同时匹配。可空 TypeAdapter 显式声明类型。
- csrf="optional" 必须与源码 csrf 调用证据匹配；游客传空字符串，有登录态则读取当前目标域 Cookie。不会吞掉客户端已关闭等其他错误。
- 人工配置的 keyword-only 参数：整数范围、字符串枚举、bool 显式 01/truefalse 编码、默认值、可省略参数、CSV 整数/字符串列表、wire 查询名与 aid/bvid 互斥。
- Rust 基础类型、Vec、Option、字符串键 HashMap、同文件优先的结构体依赖；字段 rename/alias/default 与原始标识符。alias 接受多个输入名，输出仍使用 canonical 名；同时出现时优先 canonical 名。标量响应使用严格 TypeAdapter，避免把 "false"、0 或 "1" 隐式转换成 bool/int。
- 对明确 `#[serde(default)]` 且 derive Default 的结构体，生成器把 Option/list/标量字段转换成对应 Rust Default；其他 struct-level serde 仍拒绝。父字段需要整个嵌套默认对象时继续由 `model_defaults` 显式提供。
- `external_types` 允许按 `domain:RustType` 显式复用手写跨模块模型；用于 bangumi 的公共 `VipLabel`。精确源码类型仍优先使用 `external_models`。
- user 对固定源码中两个明确自定义 serde 规则提供窄支持：MID 接受正整数或数字字符串，optional string 把空白字符串归一为 None；其他自定义反序列化继续拒绝。
- 顶层返回类型也可通过 `external_models` 直接复用手写模型；生成客户端会直接导入该模型，不要求生成模型文件中出现无用转发 import。
- 字符串参数可显式配置 nonblank=true，按源码去除首尾空白并拒绝空字符串。
- model_names 对精确源码类型路径显式重命名，external_models 显式复用手写 Pydantic 模型。未配置的类型歧义仍会失败。
- field_overrides 仅用于已复核的上游兼容差异，例如旧基线中后来变为可空或新增默认值的字段；生成结果继续通过离线 fixture 验证。
- 嵌套默认结构需显式复核值；BangumiMedia.rating 对应 Rust BangumiRating::default() 的 count=0、score=0.0。
- 从原契约查询生成测试调用 kwargs，保留原契约作为独立请求预期。
- fixed_query 明确固定字符串参数；query_copies 把已验证参数复制到协议要求的其他查询字段，例如首页推荐 fresh_idx 同步到 fresh_idx_1h/brush。

## 明确拒绝

未知或歧义类型、同名模型碰撞、递归模型、enum/tuple struct、未显式支持的自定义 serde、非字符串键 HashMap、未知签名、未复核域名、非 GET，以及与源码不符的可空/CSRF 模式。不会用 Any 替代未知模型，也不会推测参数辅助函数的含义。整数 ID 响应沿用第二波 Python int 策略，请求侧执行约束。

模型与字段的名称/路径来自清单；首批 `VideoTag` 显式选择 src/video/tags.rs，避免与 src/video/model.rs 中另一个类型混淆。默认覆盖是经审查的例外，不是从单个响应样例猜测字段是否可选。

第四批 detail 使用 src/video/model.rs 的标签类型，对外命名 VideoDetailTag；VideoView/VideoOwner/VideoStat 复用手写类型。合集分页 PageInfo 同时接受 page_num/num 与 page_size/size。

## 验证与支持状态

`tests/generated_reads/fixtures` 保存十份契约和 21 个独立响应文件，哈希见该目录 provenance.json。30 个 profile 案例中，28 个有正文，2 个仅记录 HTTP 412；后者只验证 HTTP 错误，不宣称响应模型已验证。

第四批新增八份契约和八个独立响应，24 个 profile 案例复用这些响应。全部样例哈希仍归并到 provenance.json。

生成清单中的 `status=generated` 仅说明已生成；经离线测试确认的方法再加入 `migration/python-api.json` 标记 implemented。该映射目前共 91 个方法，video 27/27、audio 20/20、bangumi 9/9、cheese 5/5、user 25/25。生成器不能把未测试的新批次自动宣称为可用。

video 收尾新增两份读取契约、四份脱敏响应。10 个无契约方法集中在手写 video/actions.py，使用源代码推导的离线请求预期与合成响应；其 validation 独立标注为 source_derived_synthetic_offline。共享核心已支持 POST/form/multipart 和显式可空 payload，读取代码生成器仍只处理 GET。

audio 使用 batch-audio.json 一次生成 16 个读取方法及 25 个响应模型；新增 16 份契约、35 个响应文件，SHA256 与固定源清单核对后并入 provenance.json。4 个写方法位于手写 audio/actions.py，API 映射中记录 source_derived_synthetic_offline、来源文件哈希及 tests/audio/test_audio.py 验证入口。模型、请求和支持范围在运行时均不依赖迁移清单。

bangumi 使用 batch-bangumi.json 补齐 season/episode 详情和 section 的生成方法与完整嵌套模型。`detail` 通用二选一入口和 `video_stream` 特殊参数/flatten 响应保留手写；播放响应复用已验证的视频 DURL/DASH/SupportFormat 组件。follow/unfollow 集中在 bangumi/actions.py，离线请求预期来自固定 Rust 源码。

cheese 使用 batch-cheese.json 生成 season/episode 详情与 episode list。通用 `info` 入口和 `video_stream` 保留手写；播放流复用视频 DASH/DURL/SupportFormat，并在 cheese 局部恢复 Rust `DashDolby.type` 的 `DefaultOnError` 语义。4 组 promoted contract family 共 16 个文件复制后逐文件 SHA256 核对并并入 provenance.json。

user 使用 batch-user.json 一次生成 16 个读取方法，覆盖 api/api.vc/api.live、两条 WBI、CSV 列表参数及完整响应模型。`UserSpaceNotice` 透明字符串和游客空对象 `UserUpStat` 使用手写模型；9 个写操作集中在 user/actions.py。16 组 promoted read contract family 共 41 个文件逐文件 SHA256 核对并加入 provenance.json；写操作继续标记 source_derived_synthetic_offline。

本批测试入口：

```powershell
uv run pytest tests/generation tests/generated_reads -q
uv run ruff check tools/migration/generate.py src/bpi tests/generation tests/generated_reads
uv run mypy tools/migration/generate.py src/bpi
```

后续扩充配置前仍需核对参数源码与类型歧义。无需重新通读整个 Rust 库，也不必每批重跑历史迁移分析测试。
