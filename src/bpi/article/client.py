from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import JsonValue, TypeAdapter

from .models import ArticleInfoData, ArticlesData, ArticleViewData, CardData, CoinResponseData
from .params import cards_query, coin_form, favorite_form, info_query, like_form, view_query

if TYPE_CHECKING:
    from bpi.client import AsyncBpiClient


_INFO = TypeAdapter(ArticleInfoData)
_VIEW = TypeAdapter(ArticleViewData)
_CARDS = TypeAdapter(CardData)
_ARTICLES = TypeAdapter(ArticlesData)
_COIN = TypeAdapter(CoinResponseData)
_OPTIONAL_JSON: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)


class ArticleClient:
    def __init__(self, client: AsyncBpiClient) -> None:
        self._client = client

    async def info(self, *, article_id: int) -> ArticleInfoData:
        return await self._client._get_payload(
            "/x/article/viewinfo",
            info_query(article_id),
            _INFO,
        )

    async def view(self, *, article_id: int, gaia_source: str = "main_web") -> ArticleViewData:
        params = await self._client._sign(view_query(article_id, gaia_source))
        return await self._client._get_payload("/x/article/view", params, _VIEW)

    async def cards(self, *, ids: str, web_location: str = "333.1305") -> CardData:
        params = await self._client._sign(cards_query(ids, web_location))
        return await self._client._get_payload("/x/article/cards", params, _CARDS)

    async def articles(self, *, article_list_id: int) -> ArticlesData:
        return await self._client._get_payload(
            "/x/article/list/web/articles",
            info_query(article_list_id),
            _ARTICLES,
        )

    async def like(self, *, article_id: int, like: bool) -> JsonValue:
        form = like_form(article_id, like, "")
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload(
            "/x/article/like",
            {},
            _OPTIONAL_JSON,
            form=form,
            optional=True,
        )

    async def coin(self, *, aid: int, upid: int, multiply: int) -> CoinResponseData:
        form = coin_form(aid, upid, multiply, "")
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload(
            "/x/web-interface/coin/add",
            {},
            _COIN,
            form=form,
        )

    async def favorite(self, *, article_id: int) -> JsonValue:
        form = favorite_form(article_id, "")
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload(
            "/x/article/favorites/add",
            {},
            _OPTIONAL_JSON,
            form=form,
            optional=True,
        )

    async def unfavorite(self, *, article_id: int) -> JsonValue:
        form = favorite_form(article_id, "")
        form["csrf"] = self._client.csrf()
        return await self._client._post_payload(
            "/x/article/favorites/del",
            {},
            _OPTIONAL_JSON,
            form=form,
            optional=True,
        )
