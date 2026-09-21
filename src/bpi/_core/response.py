from __future__ import annotations

import json
from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict, TypeAdapter, ValidationError

from bpi.errors import ApiError, AuthenticationError, MissingDataError, ResponseDecodeError

T = TypeVar("T")


class ResponseModel(BaseModel):
    model_config = ConfigDict(
        extra="ignore", strict=True, populate_by_name=True, hide_input_in_errors=True
    )


def envelope(body: bytes, *, allow_anonymous_wbi: bool = False) -> dict[str, Any]:
    try:
        raw = json.loads(body)
    except (ValueError, UnicodeError):
        raise ResponseDecodeError(body) from None
    if not isinstance(raw, dict):
        raise ResponseDecodeError(body)
    code = raw.get("code", raw.get("errno"))
    if type(code) is not int:
        raise ResponseDecodeError(body)
    if code != 0 and not (allow_anonymous_wbi and code == -101):
        message = raw.get("message", raw.get("msg", raw.get("showMsg", "")))
        error_type = AuthenticationError if ApiError(code).requires_login() else ApiError
        raise error_type(code, message if isinstance(message, str) else "")
    return raw


def decode_payload(
    body: bytes,
    adapter: TypeAdapter[T],
    *,
    allow_anonymous_wbi: bool = False,
    allow_missing: bool = False,
) -> T:
    raw = envelope(body, allow_anonymous_wbi=allow_anonymous_wbi)
    value = raw.get("data", raw.get("result"))
    if value is None and not allow_missing:
        raise MissingDataError("Successful response has no payload")
    try:
        return adapter.validate_python(value)
    except ValidationError:
        # Suppress the default chain: ValidationError may contain account or response input.
        raise ResponseDecodeError(body) from None
