from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Any

USER_AGENT = "WeirdLabPhase5/0.1 (+local research collector)"


def _get_json(url: str, timeout: int = 12) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:  # nosec - user/local research collector
        return json.loads(response.read().decode("utf-8", errors="replace"))


def _get_text(url: str, timeout: int = 12) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as response:  # nosec - user/local research collector
        return response.read().decode("utf-8", errors="replace")


def _clean(value: str | None, max_len: int = 900) -> str:
    if not value:
        return ""
    text = re.sub(r"\s+", " ", value).strip()
    return text[:max_len]


def _signal(
    *,
    title: str,
    source_type: str,
    source_url: str,
    summary: str,
    raw_text: str,
    tags: list[str],
    weirdness: int = 6,
    pain_signal: int = 6,
) -> dict[str, Any]:
    return {
        "title": _clean(title, 180),
        "source_type": source_type,
        "source_url": source_url,
        "summary": _clean(summary, 500),
        "raw_text": _clean(raw_text, 1500),
        "tags": tags,
        "weirdness": max(1, min(10, weirdness)),
        "pain_signal": max(1, min(10, pain_signal)),
    }


def collect_github(query: str, limit: int = 8) -> list[dict[str, Any]]:
    since = (datetime.now(timezone.utc) - timedelta(days=45)).strftime("%Y-%m-%d")
    q = f"{query} pushed:>{since}"
    url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(
        {"q": q, "sort": "stars", "order": "desc", "per_page": max(1, min(limit, 20))}
    )
    data = _get_json(url)
    items = data.get("items", [])[:limit]
    results = []
    for repo in items:
        stars = repo.get("stargazers_count", 0)
        language = repo.get("language") or "unknown"
        description = repo.get("description") or ""
        topics = repo.get("topics") or []
        name = repo.get("full_name") or repo.get("name") or "unknown"
        results.append(
            _signal(
                title=f"GitHub repo: {name}",
                source_type="github",
                source_url=repo.get("html_url") or "",
                summary=f"{description} Stars: {stars}. Language: {language}.",
                raw_text=f"Repo {name}\nDescription: {description}\nLanguage: {language}\nStars: {stars}\nTopics: {', '.join(topics)}\nUpdated: {repo.get('updated_at')}",
                tags=["github", "repo", language.lower(), *topics[:5]],
                weirdness=7 if stars < 500 else 5,
                pain_signal=6,
            )
        )
    return results


def collect_hn(query: str, limit: int = 8) -> list[dict[str, Any]]:
    url = "https://hn.algolia.com/api/v1/search_by_date?" + urllib.parse.urlencode(
        {"query": query, "tags": "story", "hitsPerPage": max(1, min(limit, 20))}
    )
    data = _get_json(url)
    hits = data.get("hits", [])[:limit]
    results = []
    for hit in hits:
        title = hit.get("title") or hit.get("story_title") or "HN story"
        points = hit.get("points") or 0
        comments = hit.get("num_comments") or 0
        story_url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
        results.append(
            _signal(
                title=f"HN: {title}",
                source_type="hacker_news",
                source_url=story_url,
                summary=f"HN 討論訊號。Points: {points}, comments: {comments}.",
                raw_text=f"Title: {title}\nPoints: {points}\nComments: {comments}\nURL: {story_url}\nCreated: {hit.get('created_at')}",
                tags=["hn", "discussion", "community"],
                weirdness=6,
                pain_signal=7 if comments >= 10 else 5,
            )
        )
    return results


def collect_arxiv(query: str, limit: int = 6) -> list[dict[str, Any]]:
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(
        {"search_query": f"all:{query}", "start": 0, "max_results": max(1, min(limit, 10)), "sortBy": "submittedDate", "sortOrder": "descending"}
    )
    text = _get_text(url)
    root = ET.fromstring(text)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    results = []
    for entry in root.findall("a:entry", ns)[:limit]:
        title = _clean(entry.findtext("a:title", default="arXiv paper", namespaces=ns), 220)
        summary = _clean(entry.findtext("a:summary", default="", namespaces=ns), 700)
        link = entry.findtext("a:id", default="", namespaces=ns)
        published = entry.findtext("a:published", default="", namespaces=ns)
        authors = [a.findtext("a:name", default="", namespaces=ns) for a in entry.findall("a:author", ns)]
        results.append(
            _signal(
                title=f"arXiv: {title}",
                source_type="arxiv",
                source_url=link,
                summary=summary,
                raw_text=f"Title: {title}\nAuthors: {', '.join(authors[:4])}\nPublished: {published}\nSummary: {summary}",
                tags=["arxiv", "paper", "research"],
                weirdness=8,
                pain_signal=5,
            )
        )
    return results


def fallback_signals(query: str, limit: int = 5) -> list[dict[str, Any]]:
    seeds = [
        ("失敗安裝案例", "社群常見抱怨：開源 repo README 寫得像能跑，但實際 setup 第一步就失敗。", ["failure", "setup", "repo"]),
        ("工具越來越像 dashboard", "很多 AI 工具最後都長成 dashboard / platform，缺少有記憶點的產品形狀。", ["anti-saas", "design", "product"]),
        ("AI agent 需要先讓 repo 能跑", "Coding agent 進入陌生 repo 前，build/test 環境常常是第一個阻礙。", ["agent", "build", "test"]),
        ("開源探索成本太高", "收藏很多 repo，但真的 clone、install、試用的比例很低。", ["open-source", "discovery"]),
        ("失敗也能變成產品素材", "setup/build/test 失敗 trace 本身可以變成報告、圖鑑、死因分類。", ["failure-analysis", "report"]),
    ]
    return [
        _signal(
            title=f"Fallback: {title}",
            source_type="fallback_seed",
            source_url="",
            summary=summary,
            raw_text=f"Query: {query}\nSeed: {summary}",
            tags=tags,
            weirdness=8,
            pain_signal=7,
        )
        for title, summary, tags in seeds[:limit]
    ]


COLLECTORS = {
    "github": collect_github,
    "hacker_news": collect_hn,
    "arxiv": collect_arxiv,
}


def collector_infos() -> list[dict[str, Any]]:
    return [
        {"key": "github", "label": "GitHub Repositories", "description": "搜尋近期活躍 GitHub repo，適合找開源工具素材。"},
        {"key": "hacker_news", "label": "Hacker News", "description": "搜尋 HN 最近討論，適合找社群抱怨與趨勢。"},
        {"key": "arxiv", "label": "arXiv", "description": "搜尋近期論文，適合找研究原型與奇怪方法。"},
    ]


def collect_many(sources: list[str], query: str, limit_per_source: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    results: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for source in sources:
        collector = COLLECTORS.get(source)
        if collector is None:
            errors.append({"source": source, "error": "unknown collector"})
            continue
        try:
            results.extend(collector(query=query, limit=limit_per_source))
        except Exception as exc:
            errors.append({"source": source, "error": str(exc)})
    if not results:
        results = fallback_signals(query=query, limit=min(5, max(1, limit_per_source)))
        errors.append({"source": "fallback_seed", "error": "所有線上來源都失敗，已改用內建種子素材。"})
    return results, errors
