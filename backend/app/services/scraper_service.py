import logging
import re

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

PLATFORM_SELECTORS = {
    "xiaohongshu": [".note-content", ".note-text", "#detail-desc", ".desc"],
    "mafengwo": [".article-con", ".post_info", ".travel-report", ".vc_article_content"],
    "qyer": [".bbs_post_content", ".article-content", ".forum-content"],
    "ctrip": [".ctrip_guide_content", ".detailcon", ".guide_detail"],
    "weibo": [".WB_text", ".detail_wbtext", ".weibo-text"],
    "bilibili": [".article-content", ".article-detail", ".opus-module-content"],
    "douyin": ["meta[property='og:description']"],
    "meituan": [".detail-content", ".shop-desc"],
    "dianping": [".review-content", ".comment-content"],
}

TIMEOUT = 15

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-Ch-Ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

MOBILE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/17.0 Mobile/15E148 Safari/604.1"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


def _detect_platform(url: str) -> str:
    patterns = {
        "xiaohongshu": r"xiaohongshu\.com|xhslink\.com",
        "mafengwo": r"mafengwo\.cn|mafengwo\.com",
        "qyer": r"qyer\.com",
        "ctrip": r"ctrip\.com",
        "weibo": r"weibo\.com|weibo\.cn",
        "bilibili": r"bilibili\.com|b23\.tv",
        "douyin": r"douyin\.com",
        "meituan": r"meituan\.com",
        "dianping": r"dianping\.com",
    }
    for name, pattern in patterns.items():
        if re.search(pattern, url, re.IGNORECASE):
            return name
    return "generic"


async def fetch_and_extract(url: str) -> dict:
    platform = _detect_platform(url)

    strategies = [
        (_full_scrape, BROWSER_HEADERS),
        (_full_scrape, MOBILE_HEADERS),
        (_lightweight_scrape, BROWSER_HEADERS),
        (_lightweight_scrape, MOBILE_HEADERS),
    ]

    for strategy_fn, headers in strategies:
        try:
            result = await strategy_fn(url, platform, headers)
            if result.get("text") and len(result["text"]) > 20:
                return result
        except Exception as e:
            logger.debug("Strategy %s with %s failed: %s", strategy_fn.__name__, headers.get("User-Agent", "")[:30], e)

    # Ultimate fallback: extract what we can from the URL itself
    return _url_only_fallback(url, platform)


def _url_only_fallback(url: str, platform: str) -> dict:
    """Last resort — extract hints from URL itself."""
    title = url.rstrip("/").rsplit("/", 1)[-1][:200] if "/" in url else url[:200]
    # Clean up common URL artifacts
    title = re.sub(r"[_\-\d]+$", "", title)
    title = title.replace("-", " ").replace("_", " ").strip()
    if not title or len(title) < 3:
        title = url[:200]

    return {
        "platform": platform,
        "title": title,
        "text": title,
        "images": [],
    }


async def _full_scrape(url: str, platform: str, headers: dict) -> dict:
    async with httpx.AsyncClient(
        timeout=TIMEOUT,
        follow_redirects=True,
        verify=False,
        http2=True,
    ) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")

    title = _extract_title(soup)

    selectors = PLATFORM_SELECTORS.get(platform, [])
    text = _extract_text(soup, selectors)

    if not text or len(text) < 50:
        text = _fallback_extract(soup)

    images = [img.get("src", "") for img in soup.select("img") if img.get("src")]
    images = [src for src in images[:5] if src and not src.endswith(".gif")]

    return {
        "platform": platform,
        "title": title,
        "text": text[:8000] if text else "",
        "images": images,
    }


async def _lightweight_scrape(url: str, platform: str, headers: dict) -> dict:
    async with httpx.AsyncClient(timeout=10, follow_redirects=True, verify=False) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")

    title = _extract_title(soup)
    desc = ""
    og_desc = soup.select_one("meta[property='og:description']")
    if og_desc and og_desc.get("content"):
        desc = og_desc["content"].strip()
    if not desc:
        meta_desc = soup.select_one("meta[name='description']")
        if meta_desc and meta_desc.get("content"):
            desc = meta_desc["content"].strip()

    text_parts = [title, desc] if title and desc else ([title] if title else [desc])
    text = "\n".join(text_parts) if text_parts else ""

    return {
        "platform": platform,
        "title": title,
        "text": text[:8000],
        "images": [],
    }


def _extract_title(soup: BeautifulSoup) -> str:
    og_title = soup.select_one("meta[property='og:title']")
    if og_title and og_title.get("content"):
        return og_title["content"].strip()

    tw_title = soup.select_one("meta[name='twitter:title']")
    if tw_title and tw_title.get("content"):
        return tw_title["content"].strip()

    tag = soup.select_one("h1") or soup.select_one("h2") or soup.select_one("title")
    if tag:
        text = tag.get_text(strip=True)
        if text and len(text) < 300:
            return text

    return ""


def _extract_text(soup: BeautifulSoup, selectors: list) -> str:
    for selector in selectors:
        if selector.startswith("meta"):
            tag = soup.select_one(selector)
            if tag and tag.get("content"):
                return tag["content"].strip()
            continue

        blocks = soup.select(selector)
        if blocks:
            parts = []
            for block in blocks[:3]:
                t = block.get_text(separator="\n", strip=True)
                if t:
                    parts.append(t)
            combined = "\n\n".join(parts)
            if len(combined) > 50:
                return combined

    return ""


def _fallback_extract(soup: BeautifulSoup) -> str:
    for tag_name in ["article", "main", ".content", ".article", ".post", ".detail"]:
        block = soup.select_one(tag_name)
        if block:
            txt = block.get_text(separator="\n", strip=True)
            if len(txt) > 50:
                return txt

    body = soup.body
    if body:
        text = body.get_text(separator="\n", strip=True)
        cleaned = re.sub(r"\n{3,}", "\n\n", text)
        cleaned = re.sub(r" {2,}", " ", cleaned)
        return cleaned[:5000]

    return ""
