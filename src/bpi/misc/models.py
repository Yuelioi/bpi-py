from __future__ import annotations

from pydantic import Field, JsonValue

from bpi._core.response import ResponseModel


class Buvid3Data(ResponseModel):
    buvid: str


class BuvidData(ResponseModel):
    buvid3: str = Field(alias="b_3")
    buvid4: str = Field(alias="b_4")


class ShortLinkData(ResponseModel):
    content: str
    count: int
    link: str = ""
    title: str = ""

    def extract(self) -> None:
        marker = "https://b23.tv/"
        position = self.content.find(marker)
        if position >= 0:
            self.link = self.content[position:].strip()
            self.title = self.content[:position].strip()
        else:
            self.link = ""
            self.title = self.content


class NavData(ResponseModel):
    img: str
    sub: str


class TicketData(ResponseModel):
    ticket: str
    created_at: int
    ttl: int
    context: JsonValue
    nav: NavData
