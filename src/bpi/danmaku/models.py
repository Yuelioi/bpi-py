from __future__ import annotations

import xml.etree.ElementTree as ET
import zlib

from pydantic import Field, JsonValue

from bpi._core.response import ResponseModel
from bpi.errors import ResponseDecodeError


class DanmakuPostData(ResponseModel):
    colorful_src: JsonValue | None = None
    dmid: int
    dmid_str: str


class DanmakuAdvState(ResponseModel):
    coins: int
    confirm: int = 0
    accept: bool
    has_buy: bool = Field(default=False, alias="hasBuy")


class ThumbupStatsItem(ResponseModel):
    likes: int
    user_like: int
    id_str: str


class DanmakuMeta(ResponseModel):
    time: float
    danmaku_type: int
    font_size: int
    color: int
    send_time: int
    pool_type: int
    user_hash: str
    dmid: int
    block_level: int


class Danmaku(ResponseModel):
    content: str
    p_value: str
    meta: DanmakuMeta


class DanmakuXml(ResponseModel):
    chatserver: str
    chatid: str
    mission: int
    maxlimit: int
    state: int
    real_name: int
    source: str
    danmakus: list[Danmaku]


def _float_or(value: str, default: float) -> float:
    try:
        return float(value)
    except ValueError:
        return default


def _int_or(value: str, default: int) -> int:
    try:
        return int(value)
    except ValueError:
        return default


def _parse_meta(p_value: str) -> DanmakuMeta:
    parts = p_value.split(",")
    if len(parts) < 9:
        raise ValueError("danmaku metadata requires at least 9 fields")
    return DanmakuMeta(
        time=_float_or(parts[0], 0.0),
        danmaku_type=_int_or(parts[1], 1),
        font_size=_int_or(parts[2], 25),
        color=_int_or(parts[3], 16_777_215),
        send_time=_int_or(parts[4], 0),
        pool_type=_int_or(parts[5], 0),
        user_hash=parts[6],
        dmid=_int_or(parts[7], 0),
        block_level=_int_or(parts[8], 0),
    )


def parse_deflate_danmaku_xml(body: bytes) -> DanmakuXml:
    try:
        xml = zlib.decompress(body, -zlib.MAX_WBITS).decode("utf-8")
        root = ET.fromstring(xml)
        if root.tag != "i":
            raise ValueError("unexpected root")

        def required_text(name: str) -> str:
            value = root.findtext(name)
            if value is None:
                raise ValueError(f"missing {name}")
            return value

        danmakus: list[Danmaku] = []
        for node in root.findall("d"):
            p_value = node.attrib.get("p")
            if p_value is None:
                raise ValueError("missing danmaku p attribute")
            danmakus.append(
                Danmaku(content=node.text or "", p_value=p_value, meta=_parse_meta(p_value))
            )

        return DanmakuXml(
            chatserver=required_text("chatserver"),
            chatid=required_text("chatid"),
            mission=int(required_text("mission")),
            maxlimit=int(required_text("maxlimit")),
            state=int(required_text("state")),
            real_name=int(required_text("real_name")),
            source=required_text("source"),
            danmakus=danmakus,
        )
    except (UnicodeError, ValueError, ET.ParseError, zlib.error):
        raise ResponseDecodeError(body) from None
