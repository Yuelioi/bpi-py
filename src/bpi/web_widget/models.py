from __future__ import annotations

from pydantic import TypeAdapter, ValidationError

from bpi._core.response import ResponseModel
from bpi.errors import ResponseDecodeError


class RegionBanner(ResponseModel):
    image: str
    title: str
    sub_title: str
    url: str
    rid: int


class RegionBannerData(ResponseModel):
    region_banner_list: list[RegionBanner]


class Resource(ResponseModel):
    src: str
    id: int


class Scale(ResponseModel):
    initial: float | None = None


class Rotate(ResponseModel):
    offset: int | None = None


class Translate(ResponseModel):
    offset: list[int] | None = None
    initial: list[int] | None = None


class Blur(ResponseModel):
    initial: int | None = None


class Opacity(ResponseModel):
    wrap: str
    initial: float | None = None


class Layer(ResponseModel):
    resources: list[Resource]
    scale: Scale
    rotate: Rotate
    translate: Translate
    blur: Blur
    opacity: Opacity
    id: int
    name: str


class SplitLayer(ResponseModel):
    version: str
    layers: list[Layer]


_SPLIT_LAYER = TypeAdapter(SplitLayer)


class HeaderData(ResponseModel):
    name: str
    pic: str
    litpic: str
    url: str
    is_split_layer: int
    split_layer: str
    split_layer_obj: SplitLayer | None = None

    def parse_split_layer(self) -> SplitLayer:
        try:
            parsed = _SPLIT_LAYER.validate_json(self.split_layer)
        except ValidationError:
            raise ResponseDecodeError(self.split_layer.encode()) from None
        self.split_layer_obj = parsed
        return parsed


class OnlineData(ResponseModel):
    region_count: dict[str, int]
