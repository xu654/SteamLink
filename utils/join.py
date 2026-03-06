# SteamLink/utils/join.py
from typing import Any, Dict, List, Optional

import astrbot.api.message_components as Comp
from astrbot.api import AstrBotConfig

from .steam_api import SteamAppData, SteamAPI


def _join_list(items: Optional[List[str]]) -> Optional[str]:
    if not items:
        return None
    items = [x for x in items if isinstance(x, str) and x.strip()]
    return "、".join(items) if items else None


def _join_genres(genres) -> Optional[str]:
    if not isinstance(genres, list):
        return None
    names = []
    for g in genres:
        if isinstance(g, dict) and isinstance(g.get("description"), str) and g["description"].strip():
            names.append(g["description"].strip())
    return "、".join(names) if names else None


async def build_message_chain(data: SteamAppData, config: AstrBotConfig, api: SteamAPI):
    raw = data.raw
    chain: List[Any] = []

    # 1) 封面图（最顶部）
    if bool(config.get("show_header_image", True)) and data.header_image:
        if bool(config.get("download_images", False)):
            try:
                local_path = await api.download_image(data.header_image)
                chain.append(Comp.Image.fromFileSystem(local_path))
            except Exception:
                # 下载失败则回退 URL
                chain.append(Comp.Image.fromURL(data.header_image))
        else:
            chain.append(Comp.Image.fromURL(data.header_image))

    lines: List[str] = []

    # 2) 名称（中文优先；若有英文则双语）
    if bool(config.get("show_name", True)):
        if data.name_zh and data.name_en:
            lines.append(f"🎮 {data.name_zh} / {data.name_en}")
        elif data.name_zh:
            lines.append(f"🎮 {data.name_zh}")
        elif data.name_en:
            lines.append(f"🎮 {data.name_en}")
        else:
            # 最后兜底：任意语言 name
            name_any = raw.get("name")
            if isinstance(name_any, str) and name_any.strip():
                lines.append(f"🎮 {name_any.strip()}")

    # 3) appid
    if bool(config.get("show_appid", True)):
        lines.append(f"🆔 AppID: {data.appid}")

    # 4) 类型 type: game/dlc
    if bool(config.get("show_type", True)):
        t = raw.get("type")
        if isinstance(t, str) and t.strip():
            lines.append(f"📦 类型: {t}")

    # 5) dlc 列表
    if bool(config.get("show_dlc_list", False)):
        dlc = raw.get("dlc")
        if isinstance(dlc, list) and dlc:
            # 只展示数量 + 前 N 个，避免刷屏（你也可以改成全部）
            dlc_ids = [str(x) for x in dlc if isinstance(x, int)]
            if dlc_ids:
                head = dlc_ids[:50]
                more = "" if len(dlc_ids) <= 20 else f" ...（共 {len(dlc_ids)} 个）"
                lines.append(f"🧩 DLC: {', '.join(head)}{more}")

    # 6) short_description + content_descriptors
    if bool(config.get("show_short_description", True)):
        sd = raw.get("short_description")
        if isinstance(sd, str) and sd.strip():
            lines.append(f"📝 简介: {sd.strip()}")

    if bool(config.get("show_content_descriptors", True)):
        cd = raw.get("content_descriptors")
        if isinstance(cd, dict):
            notes = cd.get("notes")
            if isinstance(notes, str) and notes.strip():
                lines.append(f"⚠️ 内容提示: {notes.strip()}")

    # 7) genres
    if bool(config.get("show_genres", True)):
        g = _join_genres(raw.get("genres"))
        if g:
            lines.append(f"🏷️ 分类: {g}")

    # 8) developers / publishers
    if bool(config.get("show_developers_publishers", True)):
        dev = _join_list(raw.get("developers"))
        pub = _join_list(raw.get("publishers"))
        if dev:
            lines.append(f"👨‍💻 开发商: {dev}")
        if pub:
            lines.append(f"🏢 发行商: {pub}")

    # 9) release_date
    if bool(config.get("show_release_date", True)):
        rd = raw.get("release_date")
        if isinstance(rd, dict):
            date = rd.get("date")
            coming = rd.get("coming_soon")
            if isinstance(date, str) and date.strip():
                if coming is True:
                    lines.append(f"📅 发售: {date.strip()}（未发售）")
                elif coming is False:
                    lines.append(f"📅 发售: {date.strip()}")
                else:
                    lines.append(f"📅 发售: {date.strip()}")

    if lines:
        chain.append(Comp.Plain("\n".join(lines)))

    return chain