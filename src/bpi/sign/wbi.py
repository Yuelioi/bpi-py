from __future__ import annotations

import hashlib
from collections.abc import Mapping
from urllib.parse import quote, urlsplit

from bpi.errors import InvalidParameterError

MIXIN = (
    46,
    47,
    18,
    2,
    53,
    8,
    23,
    32,
    15,
    50,
    10,
    31,
    58,
    3,
    45,
    35,
    27,
    43,
    5,
    49,
    33,
    9,
    42,
    19,
    29,
    28,
    14,
    39,
    12,
    38,
    41,
    13,
    37,
    48,
    7,
    16,
    24,
    55,
    40,
    61,
    26,
    17,
    0,
    1,
    60,
    51,
    30,
    4,
    22,
    25,
    54,
    21,
    56,
    59,
    6,
    63,
    57,
    62,
    11,
    36,
    20,
    34,
    44,
    52,
)


def key_from_url(url: str) -> str:
    stem, separator, extension = urlsplit(url).path.rsplit("/", 1)[-1].rpartition(".")
    if not separator or not stem or not extension:
        raise InvalidParameterError("WBI key URL must contain a filename and extension")
    return stem


def mixin_key(img_key: str, sub_key: str) -> str:
    combined = img_key + sub_key
    if not img_key or not sub_key or not combined.isascii():
        raise InvalidParameterError("Invalid WBI keys")
    result = "".join(combined[i] for i in MIXIN if i < len(combined))[:32]
    if len(result) != 32:
        raise InvalidParameterError("WBI keys cannot produce a 32-byte key")
    return result


def sign_params(
    params: Mapping[str, str], img_key: str, sub_key: str, timestamp: int
) -> dict[str, str]:
    if type(timestamp) is not int or timestamp < 0:
        raise InvalidParameterError("timestamp must be a nonnegative integer")
    if "w_rid" in params:
        raise InvalidParameterError("Parameters are already signed")
    clean = {k: v.translate(str.maketrans("", "", "!'()*")) for k, v in params.items()}
    clean["wts"] = str(timestamp)
    query = "&".join(f"{quote(k, safe='')}={quote(v, safe='')}" for k, v in sorted(clean.items()))
    clean["w_rid"] = hashlib.md5(
        (query + mixin_key(img_key, sub_key)).encode(), usedforsecurity=False
    ).hexdigest()
    return dict(sorted(clean.items()))
