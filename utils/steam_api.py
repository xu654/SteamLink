# SteamLink/utils/steam_api.py
import os
import json
import hashlib
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, List

import httpx


class SteamAPIError(Exception):
    pass


@dataclass
class SteamAppData:
    appid: int
    raw: Dict[str, Any]          # Steam 返回的 data（语言版本：优先中文）
    name_zh: Optional[str]
    name_en: Optional[str]
    header_image: Optional[str]


class SteamAPI:
    BASE = "https://store.steampowered.com/api/appdetails"

    def __init__(self, timeout_seconds: float = 8.0, download_images: bool = False):
        self._client = httpx.AsyncClient(
            timeout=timeout_seconds,
            headers={
                # 优先中文 -> 繁体 -> 英文
                "Accept-Language": "zh-CN,zh;q=0.9,zh-TW;q=0.8,en;q=0.7",
                "User-Agent": "SteamLinkAstrBot/1.0",
            },
            follow_redirects=True,
        )
        self.download_images = download_images

        # 下载缓存目录（插件目录下）
        self._img_dir = os.path.join(os.path.dirname(__file__), "..", "data", "images")
        os.makedirs(self._img_dir, exist_ok=True)

    async def close(self):
        await self._client.aclose()

    async def get_app_details(self, appid: int) -> SteamAppData:
        # 1) 优先：简中 -> 繁中 -> 英文
        raw_main, _lang_used = await self._fetch_best_language(appid)

        # 2) 额外拉一次英文，用于“中英双语名称”
        raw_en = await self._fetch(appid, lang="english")

        main_data = self._extract_data(raw_main, appid)
        en_data = self._extract_data(raw_en, appid)

        name_zh = main_data.get("name") if isinstance(main_data.get("name"), str) else None
        name_en = en_data.get("name") if isinstance(en_data.get("name"), str) else None

        # 如果中文与英文相同，就不重复显示英文
        if name_zh and name_en and name_zh.strip() == name_en.strip():
            name_en = None

        header_image = main_data.get("header_image") if isinstance(main_data.get("header_image"), str) else None

        return SteamAppData(
            appid=appid,
            raw=main_data,
            name_zh=name_zh,
            name_en=name_en,
            header_image=header_image,
        )

    async def _fetch_best_language(self, appid: int) -> Tuple[Dict[str, Any], str]:
        for lang in ("schinese", "tchinese", "english"):
            try:
                raw = await self._fetch(appid, lang=lang)
                data = self._extract_data(raw, appid)
                # 有些返回 success=true 但 data 为空的情况，这里做兜底
                if data:
                    return raw, lang
            except SteamAPIError:
                continue
        raise SteamAPIError("Steam API 返回异常（success=false 或 data 为空）")

    async def _fetch(self, appid: int, lang: str) -> Dict[str, Any]:
        params = {
            "appids": str(appid),
            "l": lang,
        }
        r = await self._client.get(self.BASE, params=params)
        if r.status_code != 200:
            raise SteamAPIError(f"HTTP {r.status_code}")
        try:
            payload = r.json()
        except Exception:
            raise SteamAPIError("响应不是合法 JSON")

        if str(appid) not in payload:
            raise SteamAPIError("响应缺少 appid 节点")

        node = payload[str(appid)]
        if not node.get("success", False):
            raise SteamAPIError("success=false（可能是无此 AppID）")

        return payload

    def _extract_data(self, payload: Dict[str, Any], appid: int) -> Dict[str, Any]:
        node = payload.get(str(appid), {})
        data = node.get("data")
        if not isinstance(data, dict):
            return {}
        return data

    async def download_image(self, url: str) -> str:
        """
        下载图片到本地，返回本地路径（用于 fromFileSystem）。
        """
        # 用 url hash 做文件名，避免 querystring 导致重复
        h = hashlib.sha1(url.encode("utf-8")).hexdigest()
        ext = ".jpg"
        path = os.path.join(self._img_dir, f"{h}{ext}")

        if os.path.exists(path) and os.path.getsize(path) > 0:
            return path

        r = await self._client.get(url)
        if r.status_code != 200:
            raise SteamAPIError(f"下载图片失败 HTTP {r.status_code}")

        with open(path, "wb") as f:
            f.write(r.content)

        return path