# SteamLink

自动识别群内 Steam 商店链接，并获取游戏信息发送到群里。

支持自动解析 Steam 链接或通过 `/查找 AppID`或者 /steam AppID 查询。

适用于 AstrBot。

---

# 功能

插件可以自动识别以下内容：

### 1 自动识别 Steam 商店链接

例如：

```

[https://store.steampowered.com/app/1551360/](https://store.steampowered.com/app/1551360/)

```
```

[https://store.steampowered.com/app/1551360?snr=5000_5100](https://store.steampowered.com/app/1551360?snr=5000_5100)__

```

发送到群内后机器人会自动返回游戏信息。

---

### 2 指令查询

```

/查找 1551360
/steam 1551360

```

机器人会查询并返回该游戏信息。

---

# 返回内容

返回内容可以在 WebUI 中自由开启或关闭。

支持内容：

- 游戏封面图
- 游戏名称（中文 + 英文）
- AppID
- 游戏类型（game / dlc）
- DLC 列表
- 游戏简介
- 内容提示（content_descriptors）
- 游戏分类
- 开发商
- 发行商
- 发售日期

---

# 限速保护

为了防止 API 被滥用：

默认限制：

```

10 分钟最多 300 次请求

```

超过后会提示：

```

已限速，请稍后再试

```

限速使用 **滚动窗口算法**。

可在 WebUI 中修改。

---

# 语言优先级

API 请求语言顺序：

```

简体中文 -> 繁体中文 -> 英文

```

如果游戏有中文和英文名称，会同时显示。

---


说明：

| 文件 | 作用 |
|----|----|
| main.py | 插件入口 |
| steam_api.py | 请求 Steam API |
| rate.py | 限速逻辑 |
| join.py | 拼接消息 |
| _conf_schema.json | WebUI 配置 |

---

# 依赖

```

httpx

```

AstrBot 会自动安装依赖。


# 使用示例

群内发送：

```

/查找 1551360

```

或

```

[https://store.steampowered.com/app/1551360/](https://store.steampowered.com/app/1551360/)

```

机器人返回：

```

🎮 极限竞速：地平线 5 / Forza Horizon 5
🆔 AppID: 1551360
📦 类型: game
🏷️ 分类: 动作、竞速、体育
👨‍💻 开发商: Playground Games
🏢 发行商: Xbox Game Studios
📅 发售: 2021 年 11 月 8 日

```

并附带封面图。

---

# 作者

xu654

GitHub：

```

[https://github.com/xu654](https://github.com/xu654)

```

---

# License

MIT
```

---
