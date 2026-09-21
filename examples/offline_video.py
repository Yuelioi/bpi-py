"""Run metadata → parts → signed playback without network access."""

import asyncio
import json
from pathlib import Path

import httpx

from bpi import AsyncBpiClient

FIXTURES = Path(__file__).resolve().parents[1] / "tests/sdk/fixtures"


async def main() -> None:
    calls: list[str] = []

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        paths = {
            "/x/web-interface/view": "video/info-read/view/responses/success.json",
            "/x/player/pagelist": "video/info-read/pagelist/responses/success.json",
            "/x/player/wbi/playurl": "video/playurl/play-url/responses/success.json",
        }
        if request.url.path == "/x/web-interface/nav":
            # Synthetic WBI keys; redacted nav fixtures cannot be used for signing.
            return httpx.Response(
                200,
                json={
                    "code": -101,
                    "data": {
                        "wbi_img": {
                            "img_url": "https://example.invalid/abcdefghijklmnopqrstuvwxyz123456.png",
                            "sub_url": "https://example.invalid/ABCDEFGHIJKLMNOPQRSTUVWXYZ654321.png",
                        }
                    },
                },
            )
        if request.url.path == "/x/player/wbi/playurl":
            assert "w_rid" in request.url.params
        return httpx.Response(200, content=(FIXTURES / paths[request.url.path]).read_bytes())

    async with AsyncBpiClient(transport=httpx.MockTransport(respond)) as client:
        video = await client.video.view(bvid="BV1xx411c7mD")
        pages = await client.video.page_list(bvid=video.bvid)
        playback = await client.video.play_url(
            bvid=video.bvid, cid=pages[0].cid, quality=32, format_flags=16
        )
        assert playback.dash and playback.dash.video
        assert calls == [
            "/x/web-interface/view",
            "/x/player/pagelist",
            "/x/web-interface/nav",
            "/x/player/wbi/playurl",
        ]
        print(
            json.dumps(
                {
                    "title": video.title,
                    "parts": len(pages),
                    "quality": playback.quality,
                    "requests": len(calls),
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
