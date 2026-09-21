"""Shared parameter validation for handwritten and generated read methods."""

import re

from bpi.errors import InvalidParameterError


def integer(value: int, name: str, minimum: int = 1) -> str:
    if type(value) is not int or value < minimum:
        raise InvalidParameterError(f"{name} must be an integer >= {minimum}")
    return str(value)


def video_id(aid: int | None, bvid: str | None, *, play: bool = False) -> dict[str, str]:
    if (aid is None) == (bvid is None):
        raise InvalidParameterError("Provide exactly one of aid or bvid")
    if aid is not None:
        return {"avid" if play else "aid": integer(aid, "aid")}
    if not isinstance(bvid, str) or not re.fullmatch(r"BV[0-9A-Za-z]{10}", bvid):
        raise InvalidParameterError("bvid must be a 12-character BV identifier")
    return {"bvid": bvid}
