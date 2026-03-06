# SteamLink/main.py
import re
import asyncio
from typing import Optional

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api import AstrBotConfig

from .utils.rate import RollingRateLimiter
from .utils.steam_api import SteamAPI, SteamAPIError
from .utils.join import build_message_chain


STEAM_APP_URL_RE = re.compile(
    r"""https?://store\.steampowered\.com/app/(\d+)(?:/|$|\?)""",
    re.IGNORECASE,
)
CMD_FIND_RE = re.compile(r"^\s*/查找\s+(\d+)\s*$", re.IGNORECASE)


@register("SteamLink", "xu654", "自动识别 Steam 链接/指令并展示游戏信息", "1.0.0")
class SteamLinkPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

        # 并发控制（避免瞬间大量请求把自己打爆）
        self._sem = asyncio.Semaphore(int(self.config.get("max_concurrency", 10)))

        # 10 分钟滚动窗口 300 次（可在 WebUI 改）
        window_sec = int(self.config.get("rate_window_seconds", 600))
        max_req = int(self.config.get("rate_max_requests", 300))
        self._limiter = RollingRateLimiter(window_seconds=window_sec, max_requests=max_req)

        # Steam API
        self._api = SteamAPI(
            timeout_seconds=float(self.config.get("http_timeout_seconds", 8.0)),
            download_images=bool(self.config.get("download_images", False)),
        )

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def on_group_message(self, event: AstrMessageEvent):
        if not bool(self.config.get("enabled", True)):
            return

        msg = (event.message_str or "").strip()
        appid = self._extract_appid(msg)
        if not appid:
            return

        # 限速：滚动窗口
        allowed, retry_after = await self._limiter.allow_async()
        if not allowed:
            tip_tpl = self.config.get("rate_limited_text", "已限速：10分钟内请求次数过多，请 {seconds}s 后重试。")
            tip = str(tip_tpl).replace("{seconds}", str(int(retry_after)))
            yield event.plain_result(tip)
            return

        async with self._sem:
            try:
                # 取数据（按：简中 -> 繁中 -> 英文；并额外拉英文名用于“双语展示”）
                data = await self._api.get_app_details(appid=int(appid))
            except SteamAPIError as e:
                logger.warning(f"SteamLink fetch failed appid={appid}: {e}")
                yield event.plain_result(f"获取 Steam 信息失败：{e}")
                return
            except Exception as e:
                logger.exception(e)
                yield event.plain_result("获取 Steam 信息失败：未知错误")
                return

        chain = await build_message_chain(
            data=data,
            config=self.config,
            api=self._api,
        )
        if chain:
            yield event.chain_result(chain)

    def _extract_appid(self, text: str) -> Optional[str]:
        # /查找 1551360
        m = CMD_FIND_RE.match(text)
        if m:
            return m.group(1)

        # Steam 商店链接
        m = STEAM_APP_URL_RE.search(text)
        if m:
            return m.group(1)

        return None

    async def terminate(self):
        await self._api.close()