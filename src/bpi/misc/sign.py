from __future__ import annotations

import hashlib
import hmac

from bpi._core.params import integer

_KEY_ID = "ec02"
_HMAC_KEY = b"XgwSnGZ1p"


def ticket_hexsign(timestamp: int) -> str:
    timestamp_text = integer(timestamp, "timestamp", minimum=0)
    return hmac.new(
        _HMAC_KEY,
        f"ts{timestamp_text}".encode(),
        hashlib.sha256,
    ).hexdigest()


def ticket_request_params(timestamp: int, csrf: str) -> dict[str, str]:
    timestamp_text = integer(timestamp, "timestamp", minimum=0)
    return {
        "key_id": _KEY_ID,
        "hexsign": ticket_hexsign(timestamp),
        "context[ts]": timestamp_text,
        "csrf": csrf,
    }
