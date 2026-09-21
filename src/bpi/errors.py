"""SDK exceptions. Sensitive input is available only through explicit attributes."""


class BpiError(Exception):
    """Base class for SDK failures."""


class InvalidParameterError(BpiError, ValueError):
    """A request parameter is invalid."""


class ClientClosedError(BpiError):
    """The client has already been closed."""


class TransportError(BpiError):
    """HTTP transport failed; the request was not automatically retried."""


class HttpStatusError(BpiError):
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(f"HTTP status {status_code}")

    def requires_login(self) -> bool:
        return self.status_code == 401

    def is_permission_error(self) -> bool:
        return self.status_code == 403

    def requires_vip(self) -> bool:
        return False

    def is_risk_control(self) -> bool:
        return self.status_code == 412

    def semantic_error(self) -> str | None:
        if self.requires_login():
            return "requires_login"
        if self.is_risk_control():
            return "risk_control"
        if self.is_permission_error():
            return "permission_denied"
        return None


class ApiError(BpiError):
    def __init__(self, code: int, message: str = "") -> None:
        self.code = code
        self.message = message  # Deliberately excluded from str/repr.
        super().__init__(f"Bilibili API error {code}")

    def requires_login(self) -> bool:
        return self.code in {-101, -401, 4_100_000, 4_511_003, 800_501_007}

    def is_risk_control(self) -> bool:
        return self.code in {-352, -412}

    def is_permission_error(self) -> bool:
        return self.code in {-403, -4}

    def requires_vip(self) -> bool:
        return self.code in {-106, -650}

    def semantic_error(self) -> str | None:
        if self.requires_login():
            return "requires_login"
        if self.requires_vip():
            return "requires_vip"
        if self.is_risk_control():
            return "risk_control"
        if self.is_permission_error():
            return "permission_denied"
        return None


class AuthenticationError(ApiError):
    """Authentication is required."""


class MissingDataError(BpiError):
    """A successful envelope is missing its required payload."""


class UnsupportedResponseError(BpiError):
    """The response format is recognized but unsupported by the current parser."""


class ResponseDecodeError(BpiError):
    def __init__(self, body: bytes) -> None:
        self.response_body = body
        super().__init__(f"Response could not be decoded ({len(body)} bytes)")
