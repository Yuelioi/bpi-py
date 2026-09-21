from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypeVar

from pydantic import TypeAdapter, ValidationError

from bpi._core.response import envelope
from bpi.errors import ResponseDecodeError

from .models import (
    Article,
    Bangumi,
    BiliUser,
    DefaultSearchData,
    HotWordDataResponse,
    LiveData,
    LiveRoom,
    LiveUser,
    Movie,
    SearchData,
    SearchSuggest,
    Video,
)
from .params import (
    CategoryId,
    Duration,
    OrderSort,
    SearchOrder,
    UserType,
    article_params,
    bangumi_params,
    bili_user_params,
    live_params,
    live_room_params,
    live_user_params,
    movie_params,
    suggest_params,
    video_params,
)

if TYPE_CHECKING:
    from bpi.client import AsyncBpiClient

T = TypeVar("T")

_TYPED_PATH = "/x/web-interface/wbi/search/type"
_DEFAULT_PATH = "/x/web-interface/wbi/search/default"
_SUGGEST_PATH = "/main/suggest"
_HOTWORDS_PATH = "/main/hotword"
_SEARCH_HOST: Literal["s.search.bilibili.com"] = "s.search.bilibili.com"

_ARTICLE = TypeAdapter(SearchData[list[Article]])
_BANGUMI = TypeAdapter(SearchData[list[Bangumi]])
_BILI_USER = TypeAdapter(SearchData[list[BiliUser]])
_LIVE = TypeAdapter(SearchData[LiveData])
_LIVE_ROOM = TypeAdapter(SearchData[list[LiveRoom]])
_LIVE_USER = TypeAdapter(SearchData[list[LiveUser]])
_MOVIE = TypeAdapter(SearchData[list[Movie]])
_VIDEO = TypeAdapter(SearchData[list[Video]])
_DEFAULT = TypeAdapter(DefaultSearchData)
_SUGGEST = TypeAdapter(SearchSuggest)
_HOTWORDS = TypeAdapter(HotWordDataResponse)


class SearchClient:
    """Public Web search API entry point."""

    def __init__(self, client: AsyncBpiClient) -> None:
        self._client = client

    async def _typed(self, params: dict[str, str], adapter: TypeAdapter[T]) -> T:
        signed = await self._client._sign(params)
        return await self._client._get_payload(_TYPED_PATH, signed, adapter)

    async def article(
        self,
        *,
        keyword: str,
        order: SearchOrder = SearchOrder.TOTAL_RANK,
        category_id: CategoryId = CategoryId.ALL,
        page: int = 1,
    ) -> SearchData[list[Article]]:
        return await self._typed(article_params(keyword, order, category_id, page), _ARTICLE)

    async def bangumi(self, *, keyword: str, page: int = 1) -> SearchData[list[Bangumi]]:
        return await self._typed(bangumi_params(keyword, page), _BANGUMI)

    async def bili_user(
        self,
        *,
        keyword: str,
        order_sort: OrderSort = OrderSort.ASCENDING,
        user_type: UserType = UserType.ALL,
        page: int = 1,
    ) -> SearchData[list[BiliUser]]:
        return await self._typed(bili_user_params(keyword, order_sort, user_type, page), _BILI_USER)

    async def live(self, *, keyword: str, page: int = 1) -> SearchData[LiveData]:
        return await self._typed(live_params(keyword, page), _LIVE)

    async def live_room(
        self,
        *,
        keyword: str,
        order: SearchOrder = SearchOrder.ONLINE,
        page: int = 1,
    ) -> SearchData[list[LiveRoom]]:
        return await self._typed(live_room_params(keyword, order, page), _LIVE_ROOM)

    async def live_user(
        self,
        *,
        keyword: str,
        order_sort: OrderSort = OrderSort.ASCENDING,
        user_type: UserType = UserType.ALL,
        page: int = 1,
    ) -> SearchData[list[LiveUser]]:
        return await self._typed(live_user_params(keyword, order_sort, user_type, page), _LIVE_USER)

    async def movie(self, *, keyword: str, page: int = 1) -> SearchData[list[Movie]]:
        return await self._typed(movie_params(keyword, page), _MOVIE)

    async def video(
        self,
        *,
        keyword: str,
        order: SearchOrder = SearchOrder.TOTAL_RANK,
        duration: Duration = Duration.ALL,
        tid: int = 0,
        page: int = 1,
    ) -> SearchData[list[Video]]:
        return await self._typed(video_params(keyword, order, duration, tid, page), _VIDEO)

    async def default(self) -> DefaultSearchData:
        params = await self._client._sign({"foo": "bar"})
        return await self._client._get_payload(_DEFAULT_PATH, params, _DEFAULT)

    async def suggest(self, *, term: str) -> SearchSuggest:
        return await self._client._get_payload(
            _SUGGEST_PATH,
            suggest_params(term),
            _SUGGEST,
            host=_SEARCH_HOST,
        )

    async def hotwords(self) -> HotWordDataResponse:
        body = await self._client._get(_HOTWORDS_PATH, {}, host=_SEARCH_HOST)
        raw = envelope(body)
        try:
            return _HOTWORDS.validate_python(raw)
        except ValidationError:
            raise ResponseDecodeError(body) from None
