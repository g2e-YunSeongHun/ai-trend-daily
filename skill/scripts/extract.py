"""URL 원문 + 발행일 일괄 추출 스크립트.

Usage:
    echo '["https://example.com/post", "https://github.com/owner/repo"]' | python extract.py
    또는
    echo -e "https://example.com/post\nhttps://github.com/owner/repo" | python extract.py

Output (stdout):
    JSON 배열 — 각 항목에 url, text, date, title, image(og:image), success, kind 포함
    kind: web | github_release | github_repo | github_file

GitHub URL은 API로 보강한다 (GITHUB_TOKEN 환경 변수가 있으면 사용).
  - /owner/repo/releases/tag/X  → 릴리스 노트, published_at
  - /owner/repo                 → 설명 + README 앞부분, 최신 릴리스 날짜(없으면 created_at), 스타 수
  - /owner/repo/blob/...        → raw 파일 본문, 날짜 없음 (CHANGELOG.md 등)
그 외 폴백 체인: trafilatura → requests(프록시·사설 CA 반영) → Playwright (headless browser)
"""

import base64
import io
import json
import os
import re
import sys

try:
    import trafilatura
except ImportError:
    trafilatura = None

try:
    import requests
except ImportError:
    requests = None

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)
_GH_API = "https://api.github.com"
_README_LIMIT = 6000

# Windows 콘솔 UTF-8 출력 보장
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")


def _use_headless_browser() -> bool:
    """기본은 headless, 디버깅 시에만 headed 브라우저 허용."""
    return os.getenv("NEWS_SCRAP_HEADED", "").strip().lower() not in {"1", "true", "yes"}


def _gh_headers() -> dict:
    headers = {"User-Agent": _UA, "Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


class _GhUnavailable(Exception):
    """API 한도 초과·네트워크 오류 등 → 일반 웹 폴백으로 넘긴다."""


class _GhNotFound(Exception):
    """존재하지 않는 레포·릴리스 → 폴백하지 않고 실패로 기록한다 (GitHub 404 페이지가 가짜 날짜를 돌려주기 때문)."""


def _gh_get(path: str, optional: bool = False):
    if requests is None:
        raise _GhUnavailable("requests 미설치")
    try:
        resp = requests.get(f"{_GH_API}{path}", headers=_gh_headers(), timeout=20)
    except Exception as e:
        raise _GhUnavailable(str(e))
    if resp.status_code == 200:
        return resp.json()
    if resp.status_code == 404:
        if optional:
            return None
        raise _GhNotFound(path)
    raise _GhUnavailable(f"HTTP {resp.status_code}")


def _day(iso: str | None) -> str | None:
    return iso[:10] if iso and len(iso) >= 10 else None


def _extract_github(url: str, result: dict) -> dict | None:
    """GitHub URL이면 API로 채운 result를 돌려주고, 아니면 None."""
    m = re.match(r"^https?://github\.com/([^/]+)/([^/#?]+)(?:/(.*))?$", url.strip())
    if not m:
        return None
    owner, repo, rest = m.group(1), m.group(2).removesuffix(".git"), (m.group(3) or "").rstrip("/")

    # 1) 릴리스 페이지
    rel = re.match(r"^releases/tag/(.+)$", rest)
    if rel:
        data = _gh_get(f"/repos/{owner}/{repo}/releases/tags/{rel.group(1)}")
        result.update(
            kind="github_release",
            title=f"{owner}/{repo} {data.get('name') or data.get('tag_name') or ''}".strip(),
            text=data.get("body") or "",
            date=_day(data.get("published_at")),
            success=bool(data.get("published_at")),
        )
        return result

    # 2) 파일(blob) → raw 본문
    blob = re.match(r"^blob/([^/]+)/(.+)$", rest)
    if blob and requests is not None:
        raw = f"https://raw.githubusercontent.com/{owner}/{repo}/{blob.group(1)}/{blob.group(2)}"
        try:
            resp = requests.get(raw, headers={"User-Agent": _UA}, timeout=20)
            if resp.status_code == 200 and resp.text.strip():
                result.update(
                    kind="github_file",
                    title=f"{owner}/{repo}/{blob.group(2)}",
                    text=resp.text[:40000],
                    date=None,
                    success=True,
                )
                return result
        except Exception:
            pass
        return None

    # 3) 레포 루트 (그 외 하위 경로는 일반 웹으로)
    if rest:
        return None
    data = _gh_get(f"/repos/{owner}/{repo}")
    latest = _gh_get(f"/repos/{owner}/{repo}/releases/latest", optional=True)
    readme = _gh_get(f"/repos/{owner}/{repo}/readme", optional=True)
    readme_text = ""
    if readme and readme.get("content"):
        try:
            readme_text = base64.b64decode(readme["content"]).decode("utf-8", "replace")
        except Exception:
            readme_text = ""
    desc = data.get("description") or ""
    parts = [p for p in (desc, readme_text[:_README_LIMIT]) if p]
    date = _day(latest.get("published_at")) if latest else None
    result.update(
        kind="github_repo",
        title=f"{owner}/{repo} (★{data.get('stargazers_count', 0)})",
        text="\n\n".join(parts),
        date=date or _day(data.get("created_at")),
        image=data.get("owner", {}).get("avatar_url", "") if isinstance(data.get("owner"), dict) else "",
        success=True,
    )
    result["github"] = {
        "stars": data.get("stargazers_count", 0),
        "created_at": _day(data.get("created_at")),
        "pushed_at": _day(data.get("pushed_at")),
        "latest_release": (latest or {}).get("tag_name"),
        "latest_release_at": date,
        "homepage": data.get("homepage") or "",
    }
    return result


def _fetch_with_requests(url: str) -> str | None:
    """trafilatura가 못 받아온 경우 requests로 재시도.

    trafilatura는 자체 urllib3 풀을 쓰기 때문에 HTTPS_PROXY와 REQUESTS_CA_BUNDLE 같은
    환경 변수를 반영하지 못한다. requests는 두 값을 모두 따르므로 프록시 뒤에서도 동작한다.
    """
    if requests is None:
        return None
    try:
        resp = requests.get(url, headers={"User-Agent": _UA}, timeout=30)
        if resp.status_code == 200:
            if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
                resp.encoding = resp.apparent_encoding
            if len(resp.text) > 500:
                return resp.text
    except Exception:
        pass
    return None


def _fetch_with_playwright(url: str) -> str | None:
    """trafilatura 실패 시 Playwright headless 브라우저로 HTML 다운로드."""
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=_use_headless_browser())
            ctx = browser.new_context(user_agent=_UA)
            page = ctx.new_page()
            page.goto(url, timeout=20000, wait_until="domcontentloaded")
            html = page.content()
            ctx.close()
            browser.close()
            if len(html) > 500:
                return html
    except Exception:
        pass
    return None


def _extract_from_html(html: str, result: dict) -> dict:
    """다운로드된 HTML에서 본문 + 메타데이터를 추출."""
    if trafilatura is None:
        return result
    text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        favor_precision=False,
        favor_recall=True,
    )
    metadata = trafilatura.extract_metadata(html)

    if text:
        result["text"] = text
        result["success"] = True

    if metadata:
        if (metadata.title or "").strip() == "Build software better, together":
            # GitHub 404 페이지. 본문·날짜 모두 무의미하다.
            result.update(text="", date=None, title="", success=False, error="github: page not found")
            return result
        result["title"] = metadata.title or ""
        result["date"] = metadata.date
        result["image"] = metadata.image or ""

    # text 없어도 date만 있으면 부분 성공
    if not text and metadata and metadata.date:
        result["success"] = True

    return result


def extract_article(url: str) -> dict:
    result = {"url": url, "text": "", "date": None, "title": "", "image": "", "success": False, "kind": "web"}
    try:
        try:
            gh = _extract_github(url, dict(result))
            if gh is not None:
                return gh
        except _GhNotFound:
            result["error"] = "github: not found (404)"
            return result
        except _GhUnavailable as e:
            result["error"] = f"github api unavailable, web fallback: {e}"

        # 1차: trafilatura 기본 fetch
        downloaded = trafilatura.fetch_url(url) if trafilatura is not None else None
        if downloaded:
            result = _extract_from_html(downloaded, result)
            if result["success"]:
                return result

        # 2차: requests (프록시·사설 CA 환경 변수 반영)
        downloaded = _fetch_with_requests(url)
        if downloaded:
            result = _extract_from_html(downloaded, result)
            if result["success"]:
                return result

        # 3차: Playwright headless 브라우저
        downloaded = _fetch_with_playwright(url)
        if downloaded:
            result = _extract_from_html(downloaded, result)

    except Exception as e:
        result["error"] = str(e)

    return result


def main():
    raw = sys.stdin.read().lstrip("﻿").strip()
    if not raw:
        print("[]")
        return

    # JSON 배열 또는 줄바꿈 구분 URL 지원
    try:
        urls = json.loads(raw)
        if isinstance(urls, str):
            urls = [urls]
    except json.JSONDecodeError:
        urls = [line.strip() for line in raw.splitlines() if line.strip()]

    results = [extract_article(url) for url in urls]
    print(json.dumps(results, ensure_ascii=False))


if __name__ == "__main__":
    main()
