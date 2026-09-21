from __future__ import annotations

from pydantic import ConfigDict, Field, RootModel

from bpi._core.response import ResponseModel


class UserSpaceNotice(RootModel[str]):
    """Transparent Rust string newtype used by /x/space/notice."""

    model_config = ConfigDict(strict=True)

    @property
    def content(self) -> str:
        return self.root


class UserUpStatArchive(ResponseModel):
    view: int = 0


class UserUpStatArticle(ResponseModel):
    view: int = 0


class UserUpStat(ResponseModel):
    """Creator statistics, including the promoted anonymous empty payload."""

    archive: UserUpStatArchive = Field(default_factory=UserUpStatArchive)
    article: UserUpStatArticle = Field(default_factory=UserUpStatArticle)
    likes: int = 0
