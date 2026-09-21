# bpi-py

[PyPI](https://pypi.org/project/bpi-py/) · [bpi-rs](https://github.com/Yuelioi/bpi-rs) · [bpi-go](https://github.com/Yuelioi/bpi-go)

一个面向 Python 的异步 Bilibili API SDK。

如果你想在 Python 里获取视频信息、搜索、用户资料、排行榜、直播、动态、评论、收藏夹、音频、番剧，或者调用登录态与创作中心接口，`bpi-py` 提供了一套统一、类型化的调用方式。

当前覆盖 **27 个领域、316 个公开方法**。

```python
import asyncio

from bpi import AsyncBpiClient


async def main() -> None:
    async with AsyncBpiClient() as client:
        video = await client.video.view(bvid="BV1xx411c7mD")
        print(video.title)
        print(video.owner.name)


asyncio.run(main())
```

## 这个项目从哪里来？

`bpi-py` 是 [`bpi-rs`](https://github.com/Yuelioi/bpi-rs) **v0.3.0** 的 Python 重构版本。

Python 版本延续了 `bpi-rs` 已经整理过的接口、参数、响应模型、特殊协议与错误语义，并针对 Python 的异步生态重新组织为 `asyncio` + HTTPX + Pydantic 的使用方式。

## 为什么用 bpi-py？

从使用者角度，主要是少写很多和 Bilibili 协议本身有关的重复代码。

| 你需要做的事 | `bpi-py` 帮你处理 |
| --- | --- |
| 调很多不同类型的 B 站接口 | 视频、用户、搜索、直播、动态、评论、收藏等都挂在同一个客户端上 |
| 手工拼 URL 和查询参数 | 使用领域方法和类型化参数 |
| 自己解析 JSON | 常用响应直接返回 Pydantic 模型 |
| 自己处理 WBI | SDK 自动完成签名和密钥缓存 |
| 自己管理 Cookie / CSRF | 登录态显式传入，写接口自动从 Cookie 中取 `bili_jct` |
| 处理 XML、deflate、protobuf、multipart | SDK 已封装对应特殊响应和上传流程 |
| 判断登录、权限、风控错误 | 提供统一的异常类型和语义判断 |
| 在爬虫 / bot / 后端里并发请求 | 基于 `asyncio` + HTTPX，直接使用异步调用 |

调用方式也比较统一：

```python
client.video.view(...)
client.search.video(...)
client.user.card(...)
client.live.room_info(...)
client.dynamic.all(...)
client.comment.list(...)
client.creativecenter.season_list(...)
```

不需要记一整套扁平函数名。

## 安装

要求 Python 3.11+。

从 PyPI 安装：

```bash
pip install bpi-py
```

使用 `uv` 安装：

```bash
uv add bpi-py
```

如果你在开发这个仓库本身，再使用 `uv sync` 安装开发环境。

运行时主要依赖：

- HTTPX
- Pydantic v2

## 示例

### 1. 获取视频信息

不需要登录。

```python
import asyncio

from bpi import AsyncBpiClient


async def main() -> None:
    async with AsyncBpiClient() as client:
        video = await client.video.view(bvid="BV1xx411c7mD")

        print(video.title)
        print(video.owner.name)
        print(video.stat.view)


asyncio.run(main())
```

也可以使用 `aid`：

```python
video = await client.video.view(aid=2)
```

### 2. 搜索视频

WBI 签名由 SDK 自动完成。

```python
async with AsyncBpiClient() as client:
    result = await client.search.video(keyword="Python", page=1)

    for video in result.result or []:
        print(video.title)
```

搜索模块还提供文章、番剧、影视、用户、直播间等分类搜索。

### 3. 获取视频排行榜

```python
async with AsyncBpiClient() as client:
    ranking = await client.video_ranking.ranking_list()

    print(ranking.note)
    print(len(ranking.list))
```

### 4. 获取直播间信息

```python
async with AsyncBpiClient() as client:
    room = await client.live.room_info(room_id=6)

    print(room.title)
    print(room.online)
```

### 5. 使用登录态

需要登录的接口显式传入 Cookie：

```python
from bpi import AsyncBpiClient


async with AsyncBpiClient(
    cookie="SESSDATA=...; bili_jct=...; DedeUserID=..."
) as client:
    nav = await client.login.nav()
    print(nav.is_login)
```

SDK 不会偷偷读取浏览器 Cookie、本地账号文件或环境里的账号信息。

需要 CSRF 的写接口会从当前 Cookie jar 中读取 `bili_jct`。

### 6. 二维码登录

```python
async with AsyncBpiClient() as client:
    qr = await client.login.qr_generate()

    print(qr.url)
    print(qr.qrcode_key)

    status = await client.login.qr_poll(qrcode_key=qr.qrcode_key)
    print(status.code)
```

SDK 负责请求和登录状态解析，二维码如何展示、多久轮询一次由你的应用决定。

## 覆盖了哪些模块？

目前公开方法已经全部映射，共 **316/316**：

| 类型 | 模块 |
| --- | --- |
| 视频与内容 | `video`、`video_ranking`、`bangumi`、`cheese`、`audio`、`article`、`note`、`opus`、`manga` |
| 用户与互动 | `user`、`comment`、`dynamic`、`message`、`fav`、`historytoview` |
| 直播 | `live` |
| 搜索 | `search` |
| 账号 | `login`、`vip`、`wallet`、`electric` |
| 创作者 | `creativecenter` |
| 其他 | `activity`、`clientinfo`、`danmaku`、`misc`、`web_widget` |

完整 Rust → Python API 映射见 [`migration/python-api.json`](migration/python-api.json)。

## 响应是类型化的

常规 API 不会只给你一个裸 `dict`：

```python
video = await client.video.view(bvid="BV1xx411c7mD")

print(video.title)
print(video.owner.name)
print(video.stat.view)
```

包内包含 `py.typed`，可以被 mypy、Pyright 等类型检查器识别。

对于 Bilibili 本身结构不稳定、上游 Rust 版本也保留为动态 JSON 的字段，Python 版本同样保留动态边界，避免为了“全类型化”而错误假设协议结构。

## 错误处理

SDK 提供统一异常：

```python
from bpi import ApiError, AuthenticationError, HttpStatusError

try:
    video = await client.video.view(aid=2)
except AuthenticationError:
    print("需要登录")
except HttpStatusError as error:
    print("HTTP:", error.status_code)
except ApiError as error:
    print("API code:", error.code)
```

常见类型包括：

- `InvalidParameterError`
- `AuthenticationError`
- `ApiError`
- `HttpStatusError`
- `TransportError`
- `MissingDataError`
- `ResponseDecodeError`
- `UnsupportedResponseError`

`ApiError` / `HttpStatusError` 还提供登录、VIP、权限、风控等稳定语义判断。

## 客户端生命周期

推荐始终使用：

```python
async with AsyncBpiClient() as client:
    ...
```

也可以手动：

```python
client = AsyncBpiClient()
try:
    ...
finally:
    await client.aclose()
```

如果传入已有的 `httpx.AsyncClient`，SDK 只借用它，不会替你关闭。

当前只提供异步客户端。

## 关于接口稳定性

Bilibili Web API 并不是官方稳定公开 API，上游字段、错误码或接口行为可能随时变化。

本项目目前主要通过来自 `bpi-rs` v0.3.0 的脱敏契约响应、请求形状和离线测试进行验证，没有为了测试而自动读取真实账号，也不会执行线上写操作。

## License

MIT License，见 [`LICENSE`](LICENSE)。

来自 `bpi-rs` 的协议、类型和测试资产沿用其 MIT 许可与归属信息，见 [`migration/SOURCE-LICENSE.txt`](migration/SOURCE-LICENSE.txt)。

