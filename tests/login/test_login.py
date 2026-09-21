from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
from urllib.parse import parse_qs

import httpx
import pytest

from bpi import AsyncBpiClient, AuthenticationError, InvalidParameterError
from bpi.login.client import LoginClient

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/generated_reads/fixtures"
LOGIN_FIXTURES = FIXTURES / "login"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("login tests must not access the live network")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)


READ_CASES = [
    ("nav", "nav", {}, "normal.success.json"),
    ("stat", "stat", {}, "normal.success.json"),
    ("coin", "coin", {}, "normal.success.json"),
    ("today-coin-exp", "today_coin_exp", {}, "normal.success.json"),
    ("daily-reward", "daily_reward", {}, "normal.success.json"),
    ("account-info", "account_info", {}, "normal.success.json"),
    ("vip-info", "vip_info", {}, "normal.success.json"),
    (
        "notice/login-notice",
        "notice",
        {"mid": 1_000_001},
        "normal.success.json",
    ),
    ("notice/login-log", "log", {}, "normal.success.json"),
    ("captcha/generate", "generate_captcha", {}, "success.json"),
    ("qr/generate", "qr_generate", {}, "anonymous.success.json"),
    (
        "qr/poll",
        "qr_poll",
        {"qrcode_key": "sanitized-qrcode-key"},
        "waiting.success.json",
    ),
]


@pytest.mark.parametrize(
    "contract_dir,method,kwargs,response_file",
    READ_CASES,
    ids=[case[0].replace("/", "-") for case in READ_CASES],
)
async def test_promoted_read_contracts(contract_dir, method, kwargs, response_file):
    fixture_dir = LOGIN_FIXTURES / contract_dir
    contract = json.loads((fixture_dir / "contract.json").read_bytes())
    body = (fixture_dir / "responses" / response_file).read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == contract["request"]["method"]
        assert str(request.url).split("?")[0] == contract["request"]["url"]
        expected_query = dict(contract["request"].get("query") or {})
        if expected_query.get("qrcode_key") == "${qrcode_key}":
            expected_query["qrcode_key"] = kwargs["qrcode_key"]
        assert dict(request.url.params) == expected_query
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(
        cookie="SESSDATA=fake", transport=httpx.MockTransport(handler)
    ) as client:
        result = await getattr(client.login, method)(**kwargs)

    assert result is not None


@pytest.mark.parametrize(
    "contract_dir,method,kwargs",
    [
        ("coin", "coin", {}),
        ("today-coin-exp", "today_coin_exp", {}),
        ("notice/login-notice", "notice", {"mid": 1_000_001}),
        ("notice/login-log", "log", {}),
    ],
)
async def test_new_private_reads_classify_anonymous_contracts(contract_dir, method, kwargs):
    body = (LOGIN_FIXTURES / contract_dir / "responses/anonymous.error.json").read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body)

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(AuthenticationError):
            await getattr(client.login, method)(**kwargs)


async def test_qr_poll_success_collects_response_cookies():
    def handler(request: httpx.Request) -> httpx.Response:
        assert dict(request.url.params) == {"qrcode_key": "qr-key"}
        return httpx.Response(
            200,
            headers=[
                ("set-cookie", "SESSDATA=session; Domain=.bilibili.com; Path=/"),
                ("set-cookie", "DedeUserID=123; Domain=.bilibili.com; Path=/"),
            ],
            json={
                "code": 0,
                "data": {
                    "url": "https://www.bilibili.com/",
                    "refresh_token": "refresh",
                    "timestamp": 1,
                    "code": 0,
                    "message": "",
                },
            },
        )

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        result = await client.login.qr_poll(qrcode_key=" qr-key ")

    assert dict(result.cookies) == {"SESSDATA": "session", "DedeUserID": "123"}


async def test_logout_source_derived_form():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "passport.bilibili.com"
        assert request.url.path == "/login/exit/v2"
        assert parse_qs(request.content.decode()) == {
            "biliCSRF": ["csrf-token"],
            "gourl": ["javascript:history.go(-1)"],
        }
        return httpx.Response(
            200,
            json={"code": 0, "data": {"redirectUrl": "https://www.bilibili.com/"}},
        )

    async with AsyncBpiClient(
        cookie="SESSDATA=fake; bili_jct=csrf-token",
        transport=httpx.MockTransport(handler),
    ) as client:
        result = await client.login.logout()
    assert result.redirect_url == "https://www.bilibili.com/"


async def test_send_sms_code_source_derived_form():
    expected = {
        "cid": ["86"],
        "tel": ["13800138000"],
        "source": ["main_web"],
        "token": ["token"],
        "challenge": ["challenge"],
        "validate": ["validate"],
        "seccode": ["validate|jordan"],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/x/passport-login/web/sms/send"
        assert parse_qs(request.content.decode()) == expected
        return httpx.Response(200, json={"code": 0, "data": {"captcha_key": "sms-key"}})

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        result = await client.login.send_sms_code(
            cid=86,
            tel="13800138000",
            token="token",
            challenge="challenge",
            validate="validate",
            seccode="validate|jordan",
        )
    assert result.captcha_key == "sms-key"


async def test_login_with_sms_source_derived_form_and_cookie_jar():
    expected = {
        "cid": ["86"],
        "tel": ["13800138000"],
        "code": ["123456"],
        "source": ["main_web"],
        "captcha_key": ["sms-key"],
        "go_url": ["https://www.bilibili.com"],
        "keep": ["true"],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/x/passport-login/web/login/sms"
        assert parse_qs(request.content.decode()) == expected
        return httpx.Response(
            200,
            headers={"set-cookie": "DedeUserID=123; Domain=.bilibili.com; Path=/"},
            json={
                "code": 0,
                "data": {"is_new": False, "status": 0, "url": "https://www.bilibili.com"},
            },
        )

    async with AsyncBpiClient(transport=httpx.MockTransport(handler)) as client:
        result = await client.login.login_with_sms(
            cid=86,
            tel=13_800_138_000,
            captcha_key="sms-key",
            code="123456",
        )
        assert client._http.cookies.get("DedeUserID") == "123"
    assert result is None


async def test_update_user_sign_source_derived_form():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/x/member/web/sign/update"
        assert parse_qs(request.content.decode()) == {
            "user_sign": ["new sign"],
            "csrf": ["csrf-token"],
        }
        return httpx.Response(200, json={"code": 0})

    async with AsyncBpiClient(
        cookie="SESSDATA=fake; bili_jct=csrf-token",
        transport=httpx.MockTransport(handler),
    ) as client:
        result = await client.login.update_user_sign(user_sign="new sign")
    assert result is None


@pytest.mark.parametrize(
    "method,kwargs",
    [
        ("notice", {"mid": 0}),
        ("notice", {"mid": 1, "buvid": " "}),
        ("log", {"jsonp": " "}),
        ("log", {"web_location": " "}),
        ("qr_poll", {"qrcode_key": " "}),
        (
            "send_sms_code",
            {
                "cid": 0,
                "tel": "13800138000",
                "token": "token",
                "challenge": "challenge",
                "validate": "validate",
                "seccode": "seccode",
            },
        ),
        (
            "send_sms_code",
            {
                "cid": 86,
                "tel": "13800138000",
                "token": " ",
                "challenge": "challenge",
                "validate": "validate",
                "seccode": "seccode",
            },
        ),
        (
            "login_with_sms",
            {"cid": 0, "tel": 13_800_138_000, "captcha_key": "key", "code": "123456"},
        ),
        ("update_user_sign", {"user_sign": "中" * 24}),
    ],
)
async def test_invalid_arguments_fail_before_network(method, kwargs):
    async with AsyncBpiClient() as client:
        with pytest.raises(InvalidParameterError):
            await getattr(client.login, method)(**kwargs)


@pytest.mark.parametrize(
    "method,kwargs",
    [
        ("logout", {}),
        ("update_user_sign", {"user_sign": "valid"}),
    ],
)
async def test_csrf_writes_require_cookie_after_validation(method, kwargs):
    async with AsyncBpiClient(cookie="SESSDATA=fake") as client:
        with pytest.raises(AuthenticationError):
            await getattr(client.login, method)(**kwargs)


def test_fixture_hashes_are_recorded():
    provenance = json.loads((FIXTURES / "provenance.json").read_bytes())
    paths = [path for path in provenance["sha256"] if path.startswith("login/")]
    assert len(paths) == 42
    for rel in paths:
        digest = hashlib.sha256((FIXTURES / rel).read_bytes()).hexdigest()
        assert digest == provenance["sha256"][rel]


def test_complete_login_mapping():
    inventory = json.loads((ROOT / "migration/generated/inventory.json").read_bytes())
    mapping = json.loads((ROOT / "migration/python-api.json").read_bytes())
    expected = {method["name"] for method in inventory["methods"] if method["domain"] == "login"}
    implemented = {
        api["python"].rsplit(".", 1)[1]
        for api in mapping["apis"]
        if api["python"].startswith("AsyncBpiClient.login.") and api["status"] == "implemented"
    }
    assert len(expected) == 16
    assert implemented == expected
    assert all(inspect.iscoroutinefunction(getattr(LoginClient, name, None)) for name in expected)
