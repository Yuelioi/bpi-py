# 私信 API

Rust 是协议基准，本地新增来源与逐文件 SHA256 见 `migration/private-message.json`；原固定 inventory 与生成配置保留，未把本地增量冒充成已发布版本。

- `client.message.sessions(session_type=SessionListType.ALL, size=100, begin_ts=None, end_ts=None)` 读取一页会话，不标记已读。
- `client.message.session_messages(talker_id=..., size=100, begin_seqno=None, end_seqno=None)` 读取一页用户私信，保留服务器顺序。
- `client.message.send(receiver_id=..., message=..., receiver_type=1)` 沿用文本/图片入口，文本拒绝空白、按嵌套 JSON 的 UTF-8 编码限制 2000 字节，保留正文换行与空白。

时间游标 `session_ts`、`begin_ts`、`end_ts` 为微秒；消息 `timestamp` 为秒；消息游标为序列号。空列表为 None，历史 `new_face_version` 可缺失，`at_uids` 可为 None；未知消息类型原样保留，正文为 JSON 字符串。

实测 `SessionListType.ALL=4` 忽略 end_ts 并重复首条；历史分页应分别查询 USER_AND_SYSTEM=1、UNFOLLOWED=2，使用上一页最小 session_ts，合并去重，并检查游标前进与 has_more。默认增量 begin_ts 的空页已经验证；SDK 不自动翻页。

发送需要 Cookie、CSRF 与 WBI，失败不自动重试，调用方须核对非零 msg_key。结果不确定时先回读确认。发送契约的样例是 `synthetic_verified_shape`，只有非零消息编号和消费项目回读曾实测，不声称完整响应已 live 验证。默认测试全部离线，本批没有重复发送。

普通会话在深分页中也可能没有最近消息，`last_msg` 可为 `None`；调用方应处理空会话。
