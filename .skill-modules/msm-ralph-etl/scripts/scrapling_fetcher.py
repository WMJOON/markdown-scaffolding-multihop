"""Scrapling-based HTTP fetcher for Ralph ETL."""
from __future__ import annotations
from typing import Tuple

from ralph.common import FetcherMode

# source_type → tier 매핑
_BASIC_TYPES = frozenset({"paper", "report", "model_card", "model_doc", "api_doc", "spec"})
_STEALTHY_TYPES = frozenset({"tech_blog", "news", "corporate_page"})

# Scrapling import is cached at module level — avoid repeated import overhead in URL loops
try:
    from scrapling.fetchers import Fetcher, StealthyFetcher, DynamicFetcher
    _scrapling_available = True
except ImportError:
    _scrapling_available = False


def _resolve_tier(fetcher_mode: str, source_type: str) -> str:
    if fetcher_mode != FetcherMode.AUTO:
        return fetcher_mode  # basic | stealthy | dynamic (명시적 지정)
    if source_type in _BASIC_TYPES:
        return FetcherMode.BASIC
    if source_type in _STEALTHY_TYPES:
        return FetcherMode.STEALTHY
    return FetcherMode.BASIC  # 기타(document 등) 기본


def _page_to_tuple(page) -> Tuple[int, str, str]:
    html = page.body.decode(page.encoding or "utf-8", errors="replace")
    return page.status, page.url, html


def fetch_with_scrapling(
    url: str,
    timeout: int = 40,
    fetcher_mode: str = FetcherMode.AUTO,
    source_type: str = "document",
) -> Tuple[int, str, str]:
    """
    Returns: (status_code: int, resolved_url: str, html_body: str)
    Scrapling 미설치 시 requests로 자동 fallback.
    """
    if not _scrapling_available:
        return _requests_fallback(url, timeout)

    tier = _resolve_tier(fetcher_mode, source_type)
    print(f"  [scrapling:{tier}] {url}")

    try:
        if tier == FetcherMode.STEALTHY:
            page = StealthyFetcher.fetch(url, timeout=timeout * 1000)
        elif tier == FetcherMode.DYNAMIC:
            page = DynamicFetcher.fetch(url, timeout=timeout * 1000)
        else:  # basic
            page = Fetcher.get(url, timeout=timeout)
        return _page_to_tuple(page)

    except Exception as exc:
        if tier == FetcherMode.STEALTHY:
            # StealthyFetcher 실패 → basic으로 재시도
            print(f"  [scrapling] stealthy failed ({exc}), retry with basic")
            return _page_to_tuple(Fetcher.get(url, timeout=timeout))
        raise


def _requests_fallback(url: str, timeout: int) -> Tuple[int, str, str]:
    import requests
    resp = requests.get(url, timeout=timeout,
                        headers={"User-Agent": "Mozilla/5.0"})
    return resp.status_code, resp.url, resp.text
