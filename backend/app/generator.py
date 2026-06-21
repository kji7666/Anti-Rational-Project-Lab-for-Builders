from __future__ import annotations

import re
from collections import Counter
from typing import Any

BORING_WORDS = {
    "dashboard",
    "saas",
    "platform",
    "marketplace",
    "workflow",
    "collaboration",
    "productivity",
    "assistant",
    "copilot",
}

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "into",
    "https",
    "http",
    "github",
    "com",
    "www",
    "tool",
    "tools",
    "agent",
    "agents",
    "ai",
    "llm",
    "open",
    "source",
    "我們",
    "你們",
    "他們",
    "以及",
    "如果",
    "這個",
    "那個",
    "可以",
    "需要",
    "使用者",
    "產品",
    "功能",
    "題目",
    "素材",
}

TEMPLATES = [
    {
        "name": "README 驗屍官",
        "one_liner": "專門把 README 寫得很美但實際跑不起來的 repo 挖出來公開驗屍。",
        "weird_angle": "不是做 repo 搜尋，而是做 README 誤導現場的屍檢檔案庫。",
        "first_screen": "輸入 repo URL 後，畫面先列出 README 承諾、實際偵測到的啟動條件、第一個失敗點與死因分類。",
        "mvp": "輸入 GitHub repo URL，解析 README、setup/build/test 訊號，產生一份可分享的屍檢報告與重跑 recipe。",
    },
    {
        "name": "Repo 急診室",
        "one_liner": "把剛抓下來的陌生 repo 丟進急診流程，判斷它是小感冒還是重症。",
        "weird_angle": "repo 不是文件夾，是送進急診的病人；setup/build/test 是生命徵象。",
        "first_screen": "每個 repo 先顯示分診結果：能不能跑、卡在哪裡、需要哪些依賴、是否缺 API key、README 是否可信。",
        "mvp": "在容器中 setup/build/test repo，失敗時分類死因並產生 markdown 屍檢報告。第一版只支援 Node/Python。",
    },
    {
        "name": "開源工具盲盒",
        "one_liner": "每天丟幾個陌生 repo 進容器，成功跑起來的是獎品，跑不起來的是怪物。",
        "weird_angle": "把開源探索變成拆盲盒：你不知道今天會得到玩具還是災難。",
        "first_screen": "今日盲盒有 5 個 repo，每個顯示存活狀態、截圖、驚喜分、危險分。",
        "mvp": "手動輸入 5 個 repo URL，系統嘗試 setup/build/start，成功的給本機網址，失敗的給原因摘要。",
    },
    {
        "name": "Agent 犯罪現場",
        "one_liner": "AI 改壞專案後，自動重建第一個失控點。",
        "weird_angle": "把 coding agent 的失敗當成犯罪現場，而不是普通錯誤 log。",
        "first_screen": "時間線顯示：誰下指令、讀了哪些檔案、第一個可疑 diff、測試何時開始失敗。",
        "mvp": "讀取 git diff、agent log、測試輸出，產生事故報告與下一輪限制 prompt。",
    },
    {
        "name": ".env 偵探",
        "one_liner": "專門找出一個 repo 到底缺哪些環境變數，哪些可以 mock，哪些是硬阻礙。",
        "weird_angle": "把環境變數當作藏在案發現場的暗號。",
        "first_screen": "畫面列出缺失的 key：可忽略、可 mock、必須人工提供、疑似文件沒寫。",
        "mvp": "掃描 README、example env、錯誤 log 與 source code，產生 env 缺口報告。",
    },
    {
        "name": "API Key 吸血鬼圖鑑",
        "one_liner": "幫你辨識哪些 repo 一打開就會吸走一堆 API key。",
        "weird_angle": "有些工具不是跑不起來，是還沒開始就要吸血。",
        "first_screen": "每個 repo 變成一隻吸血鬼卡：需要幾個 key、能否 mock、沒有 key 還能玩多少。",
        "mvp": "分析 repo 的環境需求與啟動錯誤，標記 API key 依賴程度與可試用範圍。",
    },
    {
        "name": "失敗安裝博物館",
        "one_liner": "收集各種 repo 安裝失敗案例，變成可以搜尋的失敗標本館。",
        "weird_angle": "不把失敗當垃圾，而是當標本收藏。",
        "first_screen": "展櫃顯示各種失敗標本：Node 版本錯亂、依賴消失、Dockerfile 化石、測試腐敗。",
        "mvp": "每次 repo setup 失敗都保存 log、分類、復現指令與修復建議。",
    },
    {
        "name": "Repo 怪物圖鑑",
        "one_liner": "把每個 GitHub repo 依照可馴服程度、危險程度、依賴毒性做成怪物卡。",
        "weird_angle": "repo 不是專案，是野生怪物；setup/build/test 是馴服流程。",
        "first_screen": "每張卡有怪物名、屬性、弱點、馴服指令、危險警告。",
        "mvp": "輸入 repo URL，根據檔案、依賴、setup 結果產生怪物卡與馴服步驟。",
    },
    {
        "name": "開源復活師",
        "one_liner": "找出舊但有價值的 repo，嘗試讓它重新跑起來。",
        "weird_angle": "不是追熱門，而是復活被時間埋掉的工具。",
        "first_screen": "一個復活工作台：死亡年份、腐爛依賴、復活成功率、替代指令。",
        "mvp": "輸入老 repo URL，偵測過期依賴與 runtime，嘗試用新版工具鏈建立可跑 recipe。",
    },
    {
        "name": "專題煉金爐",
        "one_liner": "把幾個無關素材丟進去，煉出怪但可做的 side project 題目。",
        "weird_angle": "靈感不是整理出來的，是把不相干材料加熱後變異出來的。",
        "first_screen": "左邊是素材罐，右邊是煉成結果：怪題、真痛點、MVP、失敗風險。",
        "mvp": "貼入 5 到 20 條素材，產生 10 張怪題卡，支援收藏、淘汰、深挖。",
    },
]


def keywords_from_text(text: str, limit: int = 8) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}|[\u4e00-\u9fff]{2,}", text.lower())
    counts = Counter(word for word in words if word not in STOPWORDS and len(word) > 1)
    return [word for word, _ in counts.most_common(limit)]


def detect_theme(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ["repo", "github", "readme", "build", "setup", "test", "container", "docker"]):
        return "repo"
    if any(word in lowered for word in ["codex", "opencode", "claude", "agent", "tool call", "mcp"]):
        return "agent"
    if any(word in lowered for word in ["ui", "visual", "figma", "website", "frontend", "game", "design"]):
        return "visual"
    return "mixed"


def pain_from_text(text: str, theme: str, keywords: list[str]) -> str:
    key_text = "、".join(keywords[:4]) or "素材"
    if theme == "repo":
        return (
            f"很多開源專案看起來值得研究，但第一步就卡在 setup/build/test；"
            f"使用者真正痛的是不知道 {key_text} 這類專案到底能不能在乾淨環境跑起來。"
        )
    if theme == "agent":
        return (
            f"AI agent 很會執行，但失敗後常缺少可追責紀錄；"
            f"使用者真正痛的是不知道 {key_text} 相關流程哪一步開始偏掉。"
        )
    if theme == "visual":
        return (
            f"視覺產品不只要功能可跑，還要畫面、風格和互動合理；"
            f"使用者真正痛的是 {key_text} 的結果很難被自動驗收。"
        )
    return (
        f"素材裡反覆出現 {key_text}，代表有一個尚未被好好命名的小痛點；"
        "需要把它從合理但無聊的產品語言裡挖出來。"
    )


def score_template(index: int, theme: str, text: str) -> dict[str, int]:
    base = {
        "surprise": 7 + (index % 3),
        "weirdness": 7 + ((index + 1) % 3),
        "memorability": 7 + ((index + 2) % 3),
        "visual_imagination": 7,
        "real_pain": 7,
        "mvp_feasibility": 7,
        "differentiation": 7,
        "personal_fit": 7,
        "anti_saas": 8,
        "revival_potential": 6,
    }
    if theme == "repo" and index in {0, 1, 2, 4, 5, 6, 7, 8}:
        base["real_pain"] += 1
        base["mvp_feasibility"] += 1
        base["personal_fit"] += 1
    if theme == "agent" and index in {3, 6, 7}:
        base["personal_fit"] += 1
        base["differentiation"] += 1
    if theme == "visual" and index in {2, 3, 6, 7, 9}:
        base["visual_imagination"] += 1
    if any(word in text.lower() for word in BORING_WORDS):
        base["surprise"] = max(1, base["surprise"] - 1)
        base["anti_saas"] = max(1, base["anti_saas"] - 2)
    return {key: min(10, value) for key, value in base.items()}


def generated_idea_payloads(
    *,
    text: str,
    source_signal_ids: list[str] | None = None,
    count: int = 10,
) -> list[dict[str, Any]]:
    source_signal_ids = source_signal_ids or []
    theme = detect_theme(text)
    keywords = keywords_from_text(text)
    pain = pain_from_text(text, theme, keywords)

    # Theme-sensitive ordering keeps the first cards closer to the supplied material.
    if theme == "repo":
        order = [0, 1, 7, 4, 5, 6, 8, 2, 9, 3]
    elif theme == "agent":
        order = [3, 0, 1, 6, 7, 9, 4, 5, 2, 8]
    elif theme == "visual":
        order = [9, 3, 2, 6, 7, 0, 1, 4, 5, 8]
    else:
        order = list(range(len(TEMPLATES)))

    ideas: list[dict[str, Any]] = []
    for position, template_index in enumerate(order[: max(1, min(count, len(TEMPLATES)))]):
        template = TEMPLATES[template_index]
        idea = {
            "name": template["name"],
            "one_liner": template["one_liner"],
            "weird_angle": template["weird_angle"],
            "real_pain": pain,
            "first_screen": template["first_screen"],
            "mvp": template["mvp"],
            "status": "new",
            "source_signal_ids": source_signal_ids,
            "scores": score_template(template_index, theme, text),
            "generator_note": f"根據素材主題 {theme} 與關鍵詞 {', '.join(keywords[:5]) or '無'} 產生。",
        }
        # Keep the original template pain if it is more concrete for generic material.
        if theme == "mixed" and position < 3:
            idea["real_pain"] = f"這個題目把素材裡的模糊訊號變成具體場景；真正要驗證的是：{pain}"
        ideas.append(idea)
    return ideas
