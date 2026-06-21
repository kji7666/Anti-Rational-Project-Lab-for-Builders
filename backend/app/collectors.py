from __future__ import annotations

import copy
import base64
import hashlib
import html
import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from typing import Any, Iterable

from .llm_client import LocalLLMError, chat_completion

USER_AGENT = "WeirdLabPhase16/0.1 (+local research collector)"
DEFAULT_RSS_FEEDS = [
    "https://hnrss.org/frontpage",
    "https://lobste.rs/rss",
    "https://feeds.feedburner.com/TheHackersNews",
    "https://www.infoq.com/feed/",
]


class SimpleHtmlTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.in_script = False
        self.in_style = False
        self.title = ""
        self.text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "title":
            self.in_title = True
        if tag == "script":
            self.in_script = True
        if tag == "style":
            self.in_style = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        if tag == "script":
            self.in_script = False
        if tag == "style":
            self.in_style = False

    def handle_data(self, data: str) -> None:
        if self.in_script or self.in_style:
            return
        text = data.strip()
        if not text:
            return
        if self.in_title and not self.title:
            self.title = text
        self.text_parts.append(text)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_json(url: str, timeout: int = 12) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:  # nosec - public research fetch
        return json.loads(response.read().decode("utf-8", errors="replace"))


def _get_text(url: str, timeout: int = 12) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as response:  # nosec - public research fetch
        return response.read().decode("utf-8", errors="replace")


def _post_form_json(
    url: str,
    form_data: dict[str, Any],
    *,
    headers: dict[str, str] | None = None,
    timeout: int = 20,
) -> dict[str, Any]:
    encoded = urllib.parse.urlencode(form_data).encode("utf-8")
    request = urllib.request.Request(url, data=encoded, method="POST", headers=headers or {})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec - official OAuth endpoint
        return json.loads(response.read().decode("utf-8", errors="replace"))


def _clean(value: str | None, max_len: int = 900) -> str:
    if not value:
        return ""
    text = html.unescape(re.sub(r"<[^>]+>", " ", value))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len]


def reddit_credentials() -> dict[str, str]:
    return {
        "client_id": os.getenv("WEIRDLAB_REDDIT_CLIENT_ID", "").strip(),
        "client_secret": os.getenv("WEIRDLAB_REDDIT_CLIENT_SECRET", "").strip(),
        "user_agent": os.getenv("WEIRDLAB_REDDIT_USER_AGENT", f"{USER_AGENT} reddit"),
        "subreddits": os.getenv("WEIRDLAB_REDDIT_SUBREDDITS", "").strip(),
    }


def reddit_enabled() -> bool:
    creds = reddit_credentials()
    return bool(creds["client_id"] and creds["client_secret"])


def contains_cjk(text: str | None) -> bool:
    return bool(text and re.search(r"[\u4e00-\u9fff]", text))


def normalize_url(url: str | None) -> str:
    if not url:
        return ""
    parsed = urllib.parse.urlsplit(url.strip())
    scheme = (parsed.scheme or "https").lower()
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/")
    query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
    filtered_pairs = [(k, v) for k, v in query_pairs if not k.lower().startswith("utm_")]
    normalized_query = urllib.parse.urlencode(filtered_pairs)
    return urllib.parse.urlunsplit((scheme, netloc, path, normalized_query, ""))


def normalize_title(title: str | None) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", (title or "").lower()).strip()


def signal_fingerprint(item: dict[str, Any]) -> str:
    url = normalize_url(item.get("source_url") or "")
    title = normalize_title(item.get("title") or "")
    source_type = (item.get("source_type") or "").strip().lower()
    summary = _clean(item.get("summary") or "", 180).lower()
    base = " | ".join(part for part in [url, title, source_type, summary] if part)
    return hashlib.sha1(base.encode("utf-8")).hexdigest() if base else ""


def _keywords_from_text(text: str, limit: int = 8) -> list[str]:
    found = re.findall(r"[A-Za-z][A-Za-z0-9_\-]{2,}|[\u4e00-\u9fff]{2,}", text or "")
    keywords: list[str] = []
    seen: set[str] = set()
    stopwords = {
        "the",
        "and",
        "for",
        "with",
        "this",
        "that",
        "from",
        "into",
        "about",
        "http",
        "https",
        "www",
        "com",
        "github",
        "repo",
        "repos",
        "article",
        "news",
        "signal",
        "素材",
        "題目",
        "工具",
        "使用者",
    }
    for token in found:
        key = token.lower()
        if key in stopwords or key in seen:
            continue
        seen.add(key)
        keywords.append(token)
        if len(keywords) >= limit:
            break
    return keywords


def score_signal_quality(item: dict[str, Any]) -> tuple[int, str]:
    score = 35
    reasons: list[str] = []

    title = _clean(item.get("title"), 200)
    summary = _clean(item.get("summary"), 600)
    raw_text = _clean(item.get("raw_text"), 1200)
    url = normalize_url(item.get("source_url"))
    tags = [str(tag).strip() for tag in item.get("tags") or [] if str(tag).strip()]

    if url:
        score += 15
        reasons.append("有可追蹤來源網址")
    if len(title) >= 12:
        score += 10
        reasons.append("標題資訊完整")
    if len(summary) >= 80:
        score += 15
        reasons.append("摘要內容充足")
    elif len(summary) >= 30:
        score += 8
        reasons.append("摘要有基本資訊")
    if len(raw_text) >= 140:
        score += 10
        reasons.append("原始內容可供後續產題")
    if len(tags) >= 3:
        score += 8
        reasons.append("標籤可用於聚類")
    if item.get("source_type") in {"github", "hacker_news", "arxiv", "rss", "devto", "lobsters"}:
        score += 5
        reasons.append("來自公開技術來源")
    if item.get("source_type") == "fallback_seed":
        score -= 20
        reasons.append("為內建補位種子")

    return max(0, min(100, score)), "、".join(reasons[:4]) or "資料品質普通"


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
    source_category: str = "",
) -> dict[str, Any]:
    item = {
        "title": _clean(title, 180),
        "source_type": source_type,
        "source_url": source_url,
        "summary": _clean(summary, 500),
        "raw_text": _clean(raw_text, 1500),
        "tags": [tag for tag in tags if tag][:8],
        "weirdness": max(1, min(10, weirdness)),
        "pain_signal": max(1, min(10, pain_signal)),
        "source_category": source_category,
    }
    quality_score, quality_reason = score_signal_quality(item)
    item["quality_score"] = quality_score
    item["quality_reason"] = quality_reason
    item["fingerprint"] = signal_fingerprint(item)
    item["collected_at"] = now_iso()
    return item


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
        stars = int(repo.get("stargazers_count") or 0)
        language = repo.get("language") or "unknown"
        description = repo.get("description") or ""
        topics = repo.get("topics") or []
        name = repo.get("full_name") or repo.get("name") or "unknown"
        open_issues = int(repo.get("open_issues_count") or 0)
        results.append(
            _signal(
                title=f"GitHub repo: {name}",
                source_type="github",
                source_url=repo.get("html_url") or "",
                summary=f"{description} Stars: {stars}。Language: {language}。Open issues: {open_issues}。",
                raw_text=(
                    f"Repo: {name}\nDescription: {description}\nLanguage: {language}\n"
                    f"Stars: {stars}\nOpen issues: {open_issues}\nTopics: {', '.join(topics)}\n"
                    f"Updated: {repo.get('updated_at')}"
                ),
                tags=["github", "repo", language.lower(), *topics[:5]],
                weirdness=7 if stars < 500 else 5,
                pain_signal=6,
                source_category="開源程式庫",
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
                summary=f"Hacker News 討論，points: {points}，comments: {comments}。",
                raw_text=f"Title: {title}\nPoints: {points}\nComments: {comments}\nURL: {story_url}\nCreated: {hit.get('created_at')}",
                tags=["hn", "discussion", "community"],
                weirdness=6,
                pain_signal=7 if comments >= 10 else 5,
                source_category="技術討論",
            )
        )
    return results


def collect_arxiv(query: str, limit: int = 6) -> list[dict[str, Any]]:
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(
        {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max(1, min(limit, 10)),
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
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
                source_category="研究論文",
            )
        )
    return results


def _filter_query_match(items: Iterable[dict[str, Any]], query: str, limit: int) -> list[dict[str, Any]]:
    keywords = [token.lower() for token in _keywords_from_text(query, limit=12)]
    if not keywords:
        return list(items)[:limit]
    ranked: list[tuple[int, dict[str, Any]]] = []
    for item in items:
        haystack = " ".join(
            [
                item.get("title", ""),
                item.get("summary", ""),
                item.get("raw_text", ""),
                " ".join(item.get("tags") or []),
            ]
        ).lower()
        matches = sum(1 for token in keywords if token in haystack)
        ranked.append((matches, item))
    ranked.sort(key=lambda pair: (pair[0], pair[1].get("quality_score") or 0), reverse=True)
    filtered = [item for matches, item in ranked if matches > 0]
    return (filtered or [item for _, item in ranked])[:limit]


def collect_rss(query: str, limit: int = 8, feed_urls: list[str] | None = None) -> list[dict[str, Any]]:
    urls = [url.strip() for url in (feed_urls or []) if url.strip()] or DEFAULT_RSS_FEEDS
    results: list[dict[str, Any]] = []
    for feed_url in urls[:8]:
        text = _get_text(feed_url)
        root = ET.fromstring(text)
        for item in root.findall(".//item")[: limit * 2]:
            title = _clean(item.findtext("title", default="RSS item"), 220)
            link = _clean(item.findtext("link", default=""), 400)
            summary = _clean(item.findtext("description", default=""), 500)
            raw_text = f"Feed: {feed_url}\nTitle: {title}\nLink: {link}\nSummary: {summary}"
            results.append(
                _signal(
                    title=f"RSS: {title}",
                    source_type="rss",
                    source_url=link,
                    summary=summary,
                    raw_text=raw_text,
                    tags=["rss", *(_keywords_from_text(title + " " + summary, limit=4))],
                    weirdness=6,
                    pain_signal=6,
                    source_category="RSS 訂閱",
                )
            )
    return _filter_query_match(results, query=query, limit=limit)


def collect_generic_urls(query: str, limit: int = 8, custom_urls: list[str] | None = None) -> list[dict[str, Any]]:
    urls = [url.strip() for url in (custom_urls or []) if url.strip()]
    results: list[dict[str, Any]] = []
    for target_url in urls[:10]:
        text = _get_text(target_url)
        parser = SimpleHtmlTextParser()
        parser.feed(text)
        combined_text = _clean(" ".join(parser.text_parts), 1500)
        title = _clean(parser.title or target_url, 220)
        summary = _clean(combined_text, 500)
        results.append(
            _signal(
                title=f"網址素材: {title}",
                source_type="generic_url",
                source_url=target_url,
                summary=summary,
                raw_text=combined_text,
                tags=["url", "custom", *(_keywords_from_text(title + " " + summary, limit=4))],
                weirdness=6,
                pain_signal=5,
                source_category="自訂網址",
            )
        )
    return _filter_query_match(results, query=query, limit=limit)


def collect_devto(query: str, limit: int = 8) -> list[dict[str, Any]]:
    url = "https://dev.to/api/articles?" + urllib.parse.urlencode({"per_page": max(1, min(limit * 3, 30)), "top": 7})
    articles = _get_json(url)
    results: list[dict[str, Any]] = []
    for article in articles[: limit * 3]:
        title = _clean(article.get("title") or "DEV article", 220)
        description = _clean(article.get("description") or "", 500)
        url_value = article.get("url") or ""
        tags = [tag.strip().lower() for tag in str(article.get("tag_list") or "").replace(",", " ").split() if tag.strip()]
        published = article.get("published_at") or ""
        positive = int(article.get("positive_reactions_count") or 0)
        comments = int(article.get("comments_count") or 0)
        results.append(
            _signal(
                title=f"DEV: {title}",
                source_type="devto",
                source_url=url_value,
                summary=description or f"DEV 社群文章，reactions: {positive}，comments: {comments}。",
                raw_text=(
                    f"Title: {title}\nDescription: {description}\nURL: {url_value}\n"
                    f"Published: {published}\nPositive reactions: {positive}\nComments: {comments}"
                ),
                tags=["devto", "article", *tags[:5]],
                weirdness=6,
                pain_signal=6,
                source_category="開發者社群",
            )
        )
    return _filter_query_match(results, query=query, limit=limit)


def collect_lobsters(query: str, limit: int = 8) -> list[dict[str, Any]]:
    text = _get_text("https://lobste.rs/rss")
    root = ET.fromstring(text)
    results: list[dict[str, Any]] = []
    for item in root.findall(".//item")[: limit * 3]:
        title = _clean(item.findtext("title", default="Lobsters item"), 220)
        link = _clean(item.findtext("link", default=""), 400)
        summary = _clean(item.findtext("description", default=""), 500)
        raw_text = f"Feed: https://lobste.rs/rss\nTitle: {title}\nLink: {link}\nSummary: {summary}"
        results.append(
            _signal(
                title=f"Lobsters: {title}",
                source_type="lobsters",
                source_url=link,
                summary=summary,
                raw_text=raw_text,
                tags=["lobsters", "community", *(_keywords_from_text(title + " " + summary, limit=4))],
                weirdness=6,
                pain_signal=6,
                source_category="技術社群",
            )
        )
    return _filter_query_match(results, query=query, limit=limit)


def reddit_access_token() -> str:
    creds = reddit_credentials()
    if not creds["client_id"] or not creds["client_secret"]:
        raise RuntimeError("Reddit collector requires WEIRDLAB_REDDIT_CLIENT_ID and WEIRDLAB_REDDIT_CLIENT_SECRET.")
    basic = base64.b64encode(f"{creds['client_id']}:{creds['client_secret']}".encode("utf-8")).decode("ascii")
    payload = _post_form_json(
        "https://www.reddit.com/api/v1/access_token",
        {"grant_type": "client_credentials"},
        headers={
            "Authorization": f"Basic {basic}",
            "User-Agent": creds["user_agent"],
            "Content-Type": "application/x-www-form-urlencoded",
        },
        timeout=20,
    )
    token = payload.get("access_token")
    if not isinstance(token, str) or not token:
        raise RuntimeError("Reddit OAuth token response did not include access_token.")
    return token


def collect_reddit(query: str, limit: int = 8) -> list[dict[str, Any]]:
    creds = reddit_credentials()
    token = reddit_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": creds["user_agent"],
        "Accept": "application/json",
    }
    subreddit_hint = creds["subreddits"]
    params = {
        "q": query,
        "sort": "new",
        "limit": max(1, min(limit, 20)),
        "t": "month",
        "type": "link",
        "raw_json": 1,
    }
    if subreddit_hint:
        params["restrict_sr"] = 1
        params["q"] = f"subreddit:{subreddit_hint} {query}"
    url = "https://oauth.reddit.com/search?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as response:  # nosec - official Reddit API
        data = json.loads(response.read().decode("utf-8", errors="replace"))

    children = data.get("data", {}).get("children", [])
    results: list[dict[str, Any]] = []
    for entry in children[:limit]:
        post = entry.get("data", {}) if isinstance(entry, dict) else {}
        title = _clean(post.get("title") or "Reddit post", 220)
        subreddit = post.get("subreddit") or "reddit"
        permalink = post.get("permalink") or ""
        post_url = f"https://www.reddit.com{permalink}" if permalink else ""
        summary = _clean(post.get("selftext") or post.get("url_overridden_by_dest") or "", 500)
        score = int(post.get("score") or 0)
        comments = int(post.get("num_comments") or 0)
        results.append(
            _signal(
                title=f"Reddit / r/{subreddit}: {title}",
                source_type="reddit",
                source_url=post_url,
                summary=summary or f"Reddit 貼文，score: {score}，comments: {comments}。",
                raw_text=(
                    f"Title: {title}\nSubreddit: {subreddit}\nScore: {score}\nComments: {comments}\n"
                    f"Author: {post.get('author')}\nCreated: {post.get('created_utc')}\n"
                    f"Body: {_clean(post.get('selftext') or '', 900)}\nURL: {post_url}"
                ),
                tags=["reddit", subreddit.lower(), *(_keywords_from_text(title + ' ' + summary, limit=4))],
                weirdness=6,
                pain_signal=7 if comments >= 10 else 5,
                source_category="社群討論",
            )
        )
    return results


def fallback_signals(query: str, limit: int = 5) -> list[dict[str, Any]]:
    seeds = [
        ("README 驗屍與落差分析", "分析 repo README 與實際 setup/build/test 的落差，找出文件承諾和可執行現實之間的斷裂點。", ["failure", "setup", "repo"]),
        ("反 SaaS 題目雷達", "觀察太像 dashboard / workflow 的題目長相，逼自己找出真正有怪味的產品方向。", ["anti-saas", "design", "product"]),
        ("AI agent repo 測試台", "把 coding agent 放進 repo build/test 流程，記錄它在哪一段最容易失控。", ["agent", "build", "test"]),
        ("開源探索失敗標本", "蒐集 clone、install、run 過程中的典型死因，整理成可搜尋的標本館。", ["open-source", "discovery"]),
        ("執行痕跡可視化", "把 setup/build/test 的錯誤與結果做成一條可讀時間線，而不是只剩散落 log。", ["failure-analysis", "report"]),
    ]
    return [
        _signal(
            title=f"補位素材: {title}",
            source_type="fallback_seed",
            source_url="",
            summary=summary,
            raw_text=f"Query: {query}\nSeed: {summary}",
            tags=tags,
            weirdness=8,
            pain_signal=7,
            source_category="內建補位",
        )
        for title, summary, tags in seeds[:limit]
    ]


COLLECTORS = {
    "github": collect_github,
    "hacker_news": collect_hn,
    "arxiv": collect_arxiv,
    "reddit": collect_reddit,
    "rss": collect_rss,
    "generic_url": collect_generic_urls,
    "devto": collect_devto,
    "lobsters": collect_lobsters,
}


def collector_infos() -> list[dict[str, Any]]:
    return [
        {
            "key": "github",
            "label": "GitHub Repositories",
            "description": "抓近期活躍的 GitHub repo，適合挖開發工具、agent 與 repo 自動化題材。",
            "category": "開源程式庫",
            "enabled": True,
            "requires_network": True,
            "requires_api_key": False,
            "risk_level": "low",
            "default_query_hint": "agent repo setup build test",
            "notes": "使用 GitHub 公開搜尋 API。",
        },
        {
            "key": "hacker_news",
            "label": "Hacker News",
            "description": "抓近期技術討論，適合看哪些題目正在被開發者社群爭論。",
            "category": "技術討論",
            "enabled": True,
            "requires_network": True,
            "requires_api_key": False,
            "risk_level": "low",
            "default_query_hint": "developer tools ai agent",
            "notes": "使用 Algolia HN API。",
        },
        {
            "key": "arxiv",
            "label": "arXiv",
            "description": "抓近期研究論文摘要，適合補進方法、模型與評測方向。",
            "category": "研究論文",
            "enabled": True,
            "requires_network": True,
            "requires_api_key": False,
            "risk_level": "low",
            "default_query_hint": "llm agent coding",
            "notes": "使用 arXiv Atom feed。",
        },
        {
            "key": "devto",
            "label": "DEV Community",
            "description": "抓開發者社群文章，補進實作觀點、踩坑經驗與最新工具用法。",
            "category": "開發者社群",
            "enabled": True,
            "requires_network": True,
            "requires_api_key": False,
            "risk_level": "low",
            "default_query_hint": "ai agent repo",
            "notes": "使用 DEV Community 公開 API。",
        },
        {
            "key": "lobsters",
            "label": "Lobsters",
            "description": "抓偏工程與工具鏈的技術社群討論，適合找較硬核的 builder 題材。",
            "category": "技術社群",
            "enabled": True,
            "requires_network": True,
            "requires_api_key": False,
            "risk_level": "low",
            "default_query_hint": "repo build test",
            "notes": "使用 Lobsters RSS，並在本地依查詢詞過濾。",
        },
        {
            "key": "reddit",
            "label": "Reddit",
            "description": "抓 Reddit 貼文與社群討論，適合挖真實痛點、吐槽與 builder 現場經驗。",
            "category": "社群討論",
            "enabled": reddit_enabled(),
            "requires_network": True,
            "requires_api_key": True,
            "risk_level": "medium",
            "default_query_hint": "ai agent repo build",
            "notes": "使用 Reddit 官方 OAuth API。請先設定 WEIRDLAB_REDDIT_CLIENT_ID / SECRET。",
        },
        {
            "key": "rss",
            "label": "RSS Feeds",
            "description": "從多個公開 feed 抓文章與消息，也可以自行補 feed URL。",
            "category": "RSS 訂閱",
            "enabled": True,
            "requires_network": True,
            "requires_api_key": False,
            "risk_level": "low",
            "default_query_hint": "tooling build test",
            "notes": "預設會抓 HN、Lobsters、Hackers News、InfoQ。",
        },
        {
            "key": "generic_url",
            "label": "自訂網址",
            "description": "讀取你指定的公開網址，把頁面文字抽成可存進素材箱的研究樣本。",
            "category": "自訂網址",
            "enabled": True,
            "requires_network": True,
            "requires_api_key": False,
            "risk_level": "medium",
            "default_query_hint": "貼上你想追的文章或專案頁",
            "notes": "只抓公開頁面文字，不執行站上腳本。",
        },
        {
            "key": "hugging_face",
            "label": "Hugging Face",
            "description": "未啟用。未來可接模型、demo 與 benchmark 素材。",
            "category": "模型社群",
            "enabled": False,
            "requires_network": True,
            "requires_api_key": False,
            "risk_level": "medium",
            "default_query_hint": "agents benchmark",
            "notes": "目前僅保留占位，不會實際抓取。",
        },
        {
            "key": "product_hunt",
            "label": "Product Hunt",
            "description": "未啟用。未來可接產品發佈動態，但通常需要額外權限。",
            "category": "產品發佈",
            "enabled": False,
            "requires_network": True,
            "requires_api_key": True,
            "risk_level": "medium",
            "default_query_hint": "developer tools",
            "notes": "需要額外 API 或授權，因此暫不開啟。",
        },
    ]


def _strip_code_fence(text: str) -> str:
    value = text.strip()
    if value.startswith("```"):
        value = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", value)
        value = re.sub(r"\s*```$", "", value)
    return value.strip()


def _translation_candidates(items: list[dict[str, Any]]) -> list[tuple[int, dict[str, Any]]]:
    candidates: list[tuple[int, dict[str, Any]]] = []
    for index, item in enumerate(items):
        title = item.get("title", "")
        summary = item.get("summary", "")
        raw_text = item.get("raw_text", "")
        if any(value and not contains_cjk(value) for value in [title, summary, raw_text]):
            candidates.append((index, item))
    return candidates


def _translate_text_public(text: str) -> str:
    cleaned = _clean(text, 700)
    if not cleaned or contains_cjk(cleaned):
        return cleaned
    url = "https://translate.googleapis.com/translate_a/single?" + urllib.parse.urlencode(
        {
            "client": "gtx",
            "sl": "auto",
            "tl": "zh-TW",
            "dt": "t",
            "q": cleaned,
        }
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as response:  # nosec - public translation fallback
        payload = json.loads(response.read().decode("utf-8", errors="replace"))
    parts = payload[0] if isinstance(payload, list) and payload else []
    translated = "".join(part[0] for part in parts if isinstance(part, list) and part and isinstance(part[0], str))
    return _clean(translated or cleaned, 700)


def _translate_chunk_public(chunk: list[tuple[int, dict[str, Any]]]) -> dict[int, dict[str, str]]:
    translated: dict[int, dict[str, str]] = {}
    for index, item in chunk:
        note_source = item.get("summary") or _clean(item.get("raw_text", ""), 280)
        translated[index] = {
            "title": _translate_text_public(item.get("title", "")),
            "summary": _translate_text_public(item.get("summary", "")),
            "notes_zh": _translate_text_public(note_source),
        }
    return translated


def _translate_chunk(chunk: list[tuple[int, dict[str, Any]]]) -> dict[int, dict[str, str]]:
    payload = [
        {
            "index": index,
            "title": item.get("title", ""),
            "summary": item.get("summary", ""),
            "raw_excerpt": _clean(item.get("raw_text", ""), 280),
        }
        for index, item in chunk
    ]
    content = chat_completion(
        messages=[
            {
                "role": "system",
                "content": (
                    "你是繁體中文技術素材翻譯器。"
                    "請把輸入陣列中的 title、summary 翻成自然的繁體中文，"
                    "並根據 raw_excerpt 寫出 1 到 2 句繁體中文重點摘要 notes_zh。"
                    "保留 repo 名稱、專有名詞、URL、數字與程式名詞。"
                    "只輸出 JSON 陣列，不要加 markdown 或解釋。"
                ),
            },
            {
                "role": "user",
                "content": json.dumps(payload, ensure_ascii=False),
            },
        ],
        temperature=0.2,
    )
    parsed = json.loads(_strip_code_fence(content))
    if not isinstance(parsed, list):
        raise LocalLLMError("Translation response was not a JSON array.")

    translated: dict[int, dict[str, str]] = {}
    for entry in parsed:
        if not isinstance(entry, dict):
            continue
        index = entry.get("index")
        if not isinstance(index, int):
            continue
        translated[index] = {
            "title": _clean(str(entry.get("title") or ""), 180),
            "summary": _clean(str(entry.get("summary") or ""), 500),
            "notes_zh": _clean(str(entry.get("notes_zh") or ""), 700),
        }
    return translated


def translate_signals_best_effort(items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    candidates = _translation_candidates(items)
    if not candidates:
        return items, []

    translated_items = [copy.deepcopy(item) for item in items]
    warnings: list[str] = []
    chunk_size = 4
    use_public_fallback = True

    for offset in range(0, len(candidates), chunk_size):
        chunk = candidates[offset : offset + chunk_size]
        try:
            translated_map = _translate_chunk_public(chunk) if use_public_fallback else _translate_chunk(chunk)
        except (LocalLLMError, json.JSONDecodeError) as exc:
            warnings.append(f"Local GPT 翻譯失敗，已改用公開翻譯備援：{exc}")
            translated_map = _translate_chunk_public(chunk)
        except Exception as exc:
            warnings.append(f"素材翻譯失敗，部分素材保留原文：{exc}")
            continue
        for index, _item in chunk:
            translated = translated_map.get(index)
            if not translated:
                continue
            if translated.get("title"):
                translated_items[index]["title"] = translated["title"]
            if translated.get("summary"):
                translated_items[index]["summary"] = translated["summary"]
            notes_zh = translated.get("notes_zh", "")
            translated_items[index]["raw_text"] = _clean(
                "\n".join(
                    part
                    for part in [
                        f"標題：{translated_items[index].get('title', '')}",
                        f"摘要：{translated_items[index].get('summary', '')}",
                        f"重點：{notes_zh}" if notes_zh else "",
                        f"來源：{translated_items[index].get('source_url', '')}" if translated_items[index].get("source_url") else "",
                    ]
                    if part
                ),
                1500,
            )
    return translated_items, warnings


def _existing_keys(existing_signals: list[dict[str, Any]]) -> tuple[set[str], set[str], set[str]]:
    existing_urls: set[str] = set()
    existing_fingerprints: set[str] = set()
    existing_title_keys: set[str] = set()
    for item in existing_signals:
        normalized_url = normalize_url(item.get("source_url"))
        if normalized_url:
            existing_urls.add(normalized_url)
        fingerprint = item.get("fingerprint") or signal_fingerprint(item)
        if fingerprint:
            existing_fingerprints.add(fingerprint)
        title_key = normalize_title(item.get("title"))
        if title_key:
            existing_title_keys.add(title_key)
    return existing_urls, existing_fingerprints, existing_title_keys


def collect_many(
    sources: list[str],
    query: str,
    limit_per_source: int,
    feed_urls: list[str] | None = None,
    custom_urls: list[str] | None = None,
    existing_signals: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    warnings: list[str] = []
    existing_urls, existing_fingerprints, existing_title_keys = _existing_keys(existing_signals or [])
    seen_urls: set[str] = set(existing_urls)
    seen_fingerprints: set[str] = set(existing_fingerprints)
    seen_title_keys: set[str] = set(existing_title_keys)

    collector_map = {item["key"]: item for item in collector_infos()}

    for source in sources:
        collector = COLLECTORS.get(source)
        meta = collector_map.get(source)
        if meta and not meta.get("enabled", True):
            warnings.append(f"{meta['label']} 目前尚未開啟，已略過。")
            continue
        if collector is None:
            errors.append({"source": source, "error": "unknown collector"})
            continue
        try:
            kwargs: dict[str, Any] = {"query": query, "limit": limit_per_source}
            if source == "rss":
                kwargs["feed_urls"] = feed_urls or []
            if source == "generic_url":
                kwargs["custom_urls"] = custom_urls or []
            collected_items = collector(**kwargs)
            for item in collected_items:
                if not item.get("fingerprint"):
                    item["fingerprint"] = signal_fingerprint(item)
                normalized_url = normalize_url(item.get("source_url"))
                fingerprint = item.get("fingerprint") or ""
                title_key = normalize_title(item.get("title"))
                is_duplicate = (
                    (normalized_url and normalized_url in seen_urls)
                    or (fingerprint and fingerprint in seen_fingerprints)
                    or (title_key and title_key in seen_title_keys)
                )
                if is_duplicate:
                    duplicates.append(item)
                    continue
                if normalized_url:
                    seen_urls.add(normalized_url)
                if fingerprint:
                    seen_fingerprints.add(fingerprint)
                if title_key:
                    seen_title_keys.add(title_key)
                results.append(item)
        except Exception as exc:
            errors.append({"source": source, "error": str(exc)})

    if "rss" in sources and not [url.strip() for url in (feed_urls or []) if url.strip()]:
        warnings.append("RSS 未提供自訂 feed URL，因此已使用預設公開 feeds。")
    if "generic_url" in sources and not [url.strip() for url in (custom_urls or []) if url.strip()]:
        warnings.append("自訂網址未提供任何 URL，因此這個來源沒有產生結果。")

    collected_count = len(results) + len(duplicates)
    if not results and not duplicates:
        results = fallback_signals(query=query, limit=min(5, max(1, limit_per_source)))
        warnings.append("目前沒有抓到可用新素材，已改用內建補位種子素材。")
    elif not results and duplicates:
        warnings.append("這次抓到的內容都和既有素材重複，因此沒有新增素材。")

    translated_results, translation_warnings = translate_signals_best_effort(results)
    translated_duplicates, duplicate_translation_warnings = translate_signals_best_effort(duplicates)
    warnings.extend(translation_warnings)
    warnings.extend(duplicate_translation_warnings)

    return {
        "signals": translated_results,
        "duplicate_signals": translated_duplicates,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "collected_count": collected_count or len(translated_results),
            "new_count": len(translated_results),
            "duplicate_count": len(translated_duplicates),
            "failed_count": len(errors),
        },
    }
