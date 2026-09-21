from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import StrictInt, TypeAdapter

from .models import (
    CollectedFolderListData,
    CreatedFolderListData,
    FavFolderInfo,
    FavListDetailData,
    FavResourceIdItem,
    ResourceInfoItem,
)
from .params import (
    clean_resources_form,
    collected_list_query,
    created_list_query,
    delete_folders_form,
    delete_resources_form,
    folder_form,
    folder_info_query,
    list_detail_query,
    resource_ids_query,
    resource_infos_query,
    transfer_form,
)

if TYPE_CHECKING:
    from bpi.client import AsyncBpiClient

_FOLDER_INFO = TypeAdapter(FavFolderInfo)
_CREATED_LIST = TypeAdapter(CreatedFolderListData)
_COLLECTED_LIST = TypeAdapter(CollectedFolderListData)
_RESOURCE_INFOS = TypeAdapter(list[ResourceInfoItem])
_LIST_DETAIL = TypeAdapter(FavListDetailData)
_RESOURCE_IDS = TypeAdapter(list[FavResourceIdItem])
_INT = TypeAdapter(StrictInt)


class FavClient:
    """Favorite-folder and favorite-resource API entry point."""

    def __init__(self, client: AsyncBpiClient) -> None:
        self._client = client

    async def folder_info(self, *, media_id: int) -> FavFolderInfo:
        return await self._client._get_payload(
            "/x/v3/fav/folder/info", folder_info_query(media_id), _FOLDER_INFO
        )

    async def created_list(
        self,
        *,
        up_mid: int,
        type_id: int | None = None,
        resource_id: int | None = None,
        web_location: str = "333.1387",
    ) -> CreatedFolderListData:
        params = created_list_query(up_mid, type_id, resource_id, web_location)
        return await self._client._get_payload(
            "/x/v3/fav/folder/created/list-all", params, _CREATED_LIST
        )

    async def collected_list(
        self,
        *,
        up_mid: int,
        page: int = 1,
        page_size: int = 20,
        platform: str = "web",
    ) -> CollectedFolderListData:
        params = collected_list_query(up_mid, page, page_size, platform)
        return await self._client._get_payload(
            "/x/v3/fav/folder/collected/list", params, _COLLECTED_LIST
        )

    async def resource_infos(
        self, *, resources: str, platform: str = "web"
    ) -> list[ResourceInfoItem]:
        params = resource_infos_query(resources, platform)
        return await self._client._get_payload("/x/v3/fav/resource/infos", params, _RESOURCE_INFOS)

    async def list_detail(
        self,
        *,
        media_id: int,
        tid: int | None = None,
        keyword: str | None = None,
        order: str | None = None,
        content_type: int | None = None,
        page_size: int = 20,
        page: int | None = None,
    ) -> FavListDetailData:
        params = list_detail_query(
            media_id,
            tid,
            keyword,
            order,
            content_type,
            page_size,
            page,
        )
        return await self._client._get_payload("/x/v3/fav/resource/list", params, _LIST_DETAIL)

    async def resource_ids(
        self, *, media_id: int, platform: str = "web"
    ) -> list[FavResourceIdItem]:
        params = resource_ids_query(media_id, platform)
        return await self._client._get_payload("/x/v3/fav/resource/ids", params, _RESOURCE_IDS)

    async def add_folder(
        self,
        *,
        title: str,
        intro: str | None = None,
        privacy: int | None = None,
        cover: str | None = None,
    ) -> FavFolderInfo:
        form = folder_form(
            csrf=self._client.csrf(),
            title=title,
            intro=intro,
            privacy=privacy,
            cover=cover,
        )
        return await self._client._post_payload("/x/v3/fav/folder/add", {}, _FOLDER_INFO, form=form)

    async def edit_folder(
        self,
        *,
        media_id: int,
        title: str,
        intro: str | None = None,
        privacy: int | None = None,
        cover: str | None = None,
    ) -> FavFolderInfo:
        form = folder_form(
            csrf=self._client.csrf(),
            media_id=media_id,
            title=title,
            intro=intro,
            privacy=privacy,
            cover=cover,
        )
        return await self._client._post_payload(
            "/x/v3/fav/folder/edit", {}, _FOLDER_INFO, form=form
        )

    async def delete_folders(self, *, media_ids: list[int]) -> int:
        form = delete_folders_form(media_ids, self._client.csrf())
        return await self._client._post_payload("/x/v3/fav/folder/del", {}, _INT, form=form)

    async def copy_resources(
        self,
        *,
        src_media_id: int,
        tar_media_id: int,
        mid: int,
        resources: str,
    ) -> int:
        form = transfer_form(
            src_media_id,
            tar_media_id,
            mid,
            resources,
            self._client.csrf(),
        )
        return await self._client._post_payload("/x/v3/fav/resource/copy", {}, _INT, form=form)

    async def move_resources(
        self,
        *,
        src_media_id: int,
        tar_media_id: int,
        mid: int,
        resources: str,
    ) -> int:
        form = transfer_form(
            src_media_id,
            tar_media_id,
            mid,
            resources,
            self._client.csrf(),
        )
        return await self._client._post_payload("/x/v3/fav/resource/move", {}, _INT, form=form)

    async def delete_resources(self, *, media_id: int, resources: str) -> int:
        form = delete_resources_form(media_id, resources, self._client.csrf())
        return await self._client._post_payload("/x/v3/fav/resource/batch-del", {}, _INT, form=form)

    async def clean_resources(self, *, media_id: int) -> int:
        form = clean_resources_form(media_id, self._client.csrf())
        return await self._client._post_payload("/x/v3/fav/resource/clean", {}, _INT, form=form)
