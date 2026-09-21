from __future__ import annotations

import re
from dataclasses import dataclass, field

from bpi.errors import InvalidParameterError


def parse_cookie(value: str) -> dict[str, str]:
    """Parse a Cookie header, retaining equals signs inside values."""
    if not isinstance(value, str) or any(ord(c) < 32 or ord(c) > 126 for c in value):
        raise InvalidParameterError("cookie must be an ASCII Cookie header")
    result = {}
    for pair in value.split(";"):
        if not pair.strip():
            continue
        name, sep, content = pair.strip().partition("=")
        if not sep or not re.fullmatch(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+", name):
            raise InvalidParameterError("cookie contains an invalid pair")
        result[name] = content
    return result


@dataclass(frozen=True)
class Account:
    sessdata: str = field(repr=False)
    bili_jct: str = field(repr=False)
    dede_user_id: str = field(default="", repr=False)
    buvid3: str = field(default="", repr=False)

    def cookie_header(self) -> str:
        pairs = {
            "SESSDATA": self.sessdata,
            "bili_jct": self.bili_jct,
            "DedeUserID": self.dede_user_id,
            "buvid3": self.buvid3,
        }
        if any(not isinstance(v, str) or ";" in v for v in pairs.values()):
            raise InvalidParameterError("account fields must be Cookie values")
        header = "; ".join(f"{k}={v}" for k, v in pairs.items() if v)
        parse_cookie(header)
        return header
