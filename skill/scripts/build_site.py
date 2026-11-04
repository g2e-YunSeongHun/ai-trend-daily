#!/usr/bin/env python3
"""누적 항목 JSON으로 docs/index.html(트렌드 피드)을 생성한다.

Usage:
  python build_site.py <items_json> <output_html> [--days 30] [--repo-url URL]

- 최근 N일(기본 30일, KST 오늘 포함) 항목만 렌더링한다.
- 상단 브리핑: 가장 최근 날짜의 하이라이트(없으면 첫 항목) + 그 날 섹션별 건수 막대 + 수집 기록 요약.
- 왼쪽 레일: 날짜(최근 7일 노출, 나머지는 "이전 N일" 접힘) · 섹션 필터. 오른쪽: 써볼 것 바구니(브라우저 저장).
- 날짜별 수집 기록 `<items_json 폴더>/runs/<날짜>.json`이 있으면 구분선에 요약과 링크를 붙인다.
- 항목 필드: 섹션, 태그, 제목, 제공자, 출처, 날짜, 날짜근거(선택), 신호(선택), 하이라이트(선택), 링크,
  관련링크(선택), 이미지(선택, 현재 미표시), 한줄정리, 왜중요, 써보기(선택), 세부(미표시), 수집일
- 제목·한줄정리·왜중요 안의 `백틱`은 <code>로 바꾼다.
"""

from __future__ import annotations

import argparse
import html
import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE = SCRIPT_DIR.parent / "templates" / "dashboard.html"
KST = timezone(timedelta(hours=9))
WEEKDAYS = "월화수목금토일"
SECTIONS = ["모델·API", "도구·에이전트", "스킬·MCP", "기법·연구"]
SEC_SLUG = {"모델·API": "model", "도구·에이전트": "tool", "스킬·MCP": "mcp", "기법·연구": "research"}
SEC_SHORT = {"모델·API": "모델", "도구·에이전트": "도구", "스킬·MCP": "MCP", "기법·연구": "기법"}
SEC_COLOR = {"model": "#1D4ED8", "tool": "#0F766E", "mcp": "#B45309", "research": "#BE185D"}
SEC_ORDER = {s: i for i, s in enumerate(SECTIONS)}
TAGS = {"신규출시", "업데이트", "오픈소스", "실전팁"}
DEFAULT_REPO_URL = "https://github.com/g2e-YunSeongHun/ai-trend-daily"
VISIBLE_DAYS = 7
_TICK = re.compile(r"`([^`\n]+)`")


def esc(v) -> str:
    return html.escape(str(v or "").strip())


def attr(v) -> str:
    return html.escape(str(v or "").strip(), quote=True)


def rich(v) -> str:
    """HTML 이스케이프 후 `백틱`을 <code>로 바꾼다."""
    return _TICK.sub(r"<code>\1</code>", esc(v))


def plain(v) -> str:
    """백틱만 제거한 평문 (브리핑 블록처럼 code 서식이 어색한 곳)."""
    return esc(str(v or "").replace("`", ""))


def fmt_long(d: date) -> str:
    return f"{d.year}년 {d.month}월 {d.day}일 ({WEEKDAYS[d.weekday()]})"


def fmt_short(iso: str) -> str:
    try:
        d = date.fromisoformat(iso)
        return f"{d.month}월 {d.day}일 ({WEEKDAYS[d.weekday()]})"
    except ValueError:
        return esc(iso)


def tag_of(a: dict) -> str:
    t = str(a.get("태그", "")).strip()
    return t if t in TAGS else "업데이트"


def sec_of(a: dict) -> str:
    s = str(a.get("섹션", "")).strip()
    return s if s in SEC_SLUG else SECTIONS[-1]


def is_highlight(a: dict) -> bool:
    return bool(a.get("하이라이트"))


def search_text(a: dict) -> str:
    parts = [a.get(k, "") for k in ("제목", "제공자", "출처", "한줄정리", "왜중요", "써보기", "신호")]
    return attr(" ".join(str(p) for p in parts if p).lower())


def links_html(raw) -> str:
    if not raw:
        return ""
    out = []
    for item in raw[:3]:
        if isinstance(item, dict):
            url, label = str(item.get("url", "")).strip(), str(item.get("라벨", "")).strip()
        else:
            url, label = str(item).strip(), ""
        if not url:
            continue
        if not label:
            label = urlsplit(url).netloc.removeprefix("www.") or url
        out.append(f'<a class="rel" href="{attr(url)}" target="_blank" rel="noreferrer">{esc(label)}</a>')
    return "".join(out)


def item_html(a: dict, is_new: bool) -> str:
    sec, tag = sec_of(a), tag_of(a)
    slug = SEC_SLUG[sec]
    url = str(a.get("링크", "")).strip()
    href = attr(url) if url else "#"
    meta = [f'<span class="sec sec-{slug}">{esc(sec)}</span>', f'<span class="tag">{tag}</span>']
    if a.get("제공자"):
        meta.append(f"<span>{esc(a['제공자'])}</span>")
    if is_highlight(a):
        meta.insert(0, '<span class="hl-label">하이라이트</span>')
    if is_new:
        meta.insert(0, '<span class="new">NEW</span>')
    if a.get("날짜근거"):
        meta.append(f'<span class="basis">{esc(a["날짜근거"])}</span>')

    why = rich(a.get("왜중요"))
    why_html = f'<p class="why">{why}</p>' if why else ""
    ev = []
    if a.get("신호"):
        ev.append(f'<span class="ev"><b>{esc(a["신호"])}</b></span>')
    if a.get("출처"):
        ev.append(f'<span class="ev">{esc(a["출처"])}</span>')
    ev_html = f'<div class="evrow"><span class="k">근거</span>{"".join(ev)}</div>' if ev else ""
    try_code = str(a.get("써보기", "")).strip()
    try_html = (
        f'<div class="try" aria-label="써보기 명령"><code>{esc(try_code)}</code>'
        f'<button type="button" class="copy" aria-label="명령 복사">복사</button></div>'
        if try_code else ""
    )
    rel = links_html(a.get("관련링크"))
    classes = ["card"] + (["hl"] if is_highlight(a) else [])
    return (
        f'<article class="{" ".join(classes)}" data-key="{attr(url)}" data-sec="{attr(sec)}" data-secclass="sec-{slug}" '
        f'data-secshort="{SEC_SHORT[sec]}" data-date="{attr(a.get("날짜"))}" data-text="{search_text(a)}">'
        f'<div class="meta">{" ".join(meta)}</div>'
        f'<h3><a href="{href}" target="_blank" rel="noreferrer">{rich(a.get("제목", "제목 미상"))}</a></h3>'
        f'<p class="one">{rich(a.get("한줄정리") or "원문 미확보")}</p>'
        f"{why_html}{ev_html}{try_html}"
        f'<div class="foot">'
        f'<button type="button" class="icon-btn b-book"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 3h12v18l-6-4-6 4z"/></svg><span>써볼 것에 담기</span></button>'
        f'<button type="button" class="icon-btn b-read"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6L9 17l-5-5"/></svg><span>읽음 표시</span></button>'
        f"{rel}"
        f'<a class="open" href="{href}" target="_blank" rel="noreferrer">원문 열기 ↗</a>'
        f"</div></article>"
    )


def load_run(runs_dir: Path, iso: str) -> dict | None:
    p = runs_dir / f"{iso}.json"
    if not p.exists():
        return None
    try:
        with p.open(encoding="utf-8-sig") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None


def run_summary(run: dict | None) -> tuple[str, int, int, int, int]:
    if not run:
        return "", 0, 0, 0, 0
    srcs = len(run.get("sources_checked") or [])
    cands = run.get("candidates") or []
    inc = sum(1 for c in cands if c.get("decision") == "포함")
    unavail = len(run.get("unavailable") or [])
    bits = [f"출처 {srcs}곳 확인", f"후보 {len(cands)}건 → {inc}건"]
    if unavail:
        bits.append(f"미확인 {unavail}곳")
    return " · ".join(bits), srcs, len(cands), inc, unavail


def day_html(iso: str, n: int, run: dict | None, repo_url: str) -> str:
    summary = run_summary(run)[0]
    log = (
        f'<a class="log" href="{attr(repo_url)}/blob/main/data/runs/{attr(iso)}.json" target="_blank" rel="noreferrer" '
        f'title="이 날의 수집 기록(확인한 출처·제외 사유)">{summary}</a>'
        if summary else ""
    )
    return f'<div class="day" id="d-{attr(iso)}"><h2>{fmt_short(iso)}</h2><span class="n">{n}건</span>{log}<span class="line"></span></div>'


def brief_html(latest_iso: str, latest_items: list[dict], run: dict | None, repo_url: str) -> str:
    if not latest_items:
        return ""
    hl = next((a for a in latest_items if is_highlight(a)), latest_items[0])
    sec = sec_of(hl)
    ev = []
    if hl.get("신호"):
        ev.append(f'<span class="ev"><b>{esc(hl["신호"])}</b> {esc(hl.get("출처"))}</span>')
    ev.append(f'<span class="ev">{esc(sec)}</span>')
    counts = {s: sum(1 for a in latest_items if sec_of(a) == s) for s in SECTIONS}
    mx = max(counts.values()) or 1
    rows = []
    for s in SECTIONS:
        slug = SEC_SLUG[s]
        pct = int(round(counts[s] / mx * 100))
        rows.append(
            f'<div class="row"><span class="sec sec-{slug}">{esc(s)}</span>'
            f'<div class="bar"><i style="width:{pct}%;background:{SEC_COLOR[slug]}"></i></div><b>{counts[s]}</b></div>'
        )
    summary = run_summary(run)[0]
    log = (
        f'<div class="log">{summary} <a href="{attr(repo_url)}/blob/main/data/runs/{attr(latest_iso)}.json" target="_blank" rel="noreferrer">수집 기록</a></div>'
        if summary else '<div class="log"></div>'
    )
    return (
        '<section class="brief" aria-label="오늘의 브리핑">'
        f'<div class="hl-box"><div class="k"><b>오늘의 하이라이트</b><span>{fmt_short(latest_iso)}</span>'
        f'<span class="since"><i></i><span id="since"></span></span></div>'
        f'<h2><a href="{attr(hl.get("링크"))}" target="_blank" rel="noreferrer">{plain(hl.get("제목"))}</a></h2>'
        f'<p>{plain(hl.get("한줄정리"))}</p>'
        f'<div class="evrow" style="margin-top:auto">{"".join(ev)}</div></div>'
        f'<div class="radar"><div class="k">어제 어디가 움직였나</div><div style="display:flex;flex-direction:column;gap:10px">{"".join(rows)}</div>{log}</div>'
        "</section>"
    )


def dates_html(day_counts: list[tuple[str, int]]) -> str:
    out = []
    hidden = 0
    for i, (iso, n) in enumerate(day_counts):
        old = i >= VISIBLE_DAYS
        if old:
            hidden += 1
        out.append(
            f'<button type="button" class="rail-btn" data-d="{attr(iso)}"{" data-old=\"1\" hidden" if old else ""}>'
            f"<span>{fmt_short(iso)}</span><span class=\"n\">{n}</span></button>"
        )
    if hidden:
        out.append(f'<button type="button" class="rail-btn more" id="dates-more">이전 {hidden}일 ▸</button>')
    return "\n".join(out)


def secs_html(recent: list[dict]) -> str:
    out = [f'<button type="button" class="rail-btn on" data-v=""><span>전체</span><span class="n">{len(recent)}</span></button>']
    for s in SECTIONS:
        n = sum(1 for a in recent if sec_of(a) == s)
        out.append(
            f'<button type="button" class="rail-btn" data-v="{attr(s)}"><span class="sec sec-{SEC_SLUG[s]}" style="font-size:14px;font-weight:500">{esc(s)}</span><span class="n">{n}</span></button>'
        )
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("items_json")
    ap.add_argument("output_html")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--repo-url", default=DEFAULT_REPO_URL)
    args = ap.parse_args()
    repo_url = args.repo_url.rstrip("/")

    items_path = Path(args.items_json)
    with items_path.open(encoding="utf-8-sig") as fh:
        items = json.load(fh)
    runs_dir = items_path.parent / "runs"

    today = datetime.now(KST).date()
    start_iso = (today - timedelta(days=args.days - 1)).isoformat()
    recent = [a for a in items if str(a.get("날짜", "")) >= start_iso]
    # 날짜 desc → 하이라이트 먼저 → 섹션 순서 → 제공자 → 제목
    recent.sort(key=lambda a: (a.get("제공자", ""), a.get("제목", "")))
    recent.sort(key=lambda a: SEC_ORDER.get(sec_of(a), len(SECTIONS)))
    recent.sort(key=lambda a: not is_highlight(a))
    recent.sort(key=lambda a: a.get("날짜", ""), reverse=True)

    latest_run = max((str(a.get("수집일", "")) for a in recent), default="")
    per_day: dict[str, int] = {}
    for a in recent:
        per_day[str(a.get("날짜", ""))] = per_day.get(str(a.get("날짜", "")), 0) + 1
    day_counts = sorted(per_day.items(), reverse=True)

    parts: list[str] = []
    cur = None
    new_count = 0
    for a in recent:
        d = str(a.get("날짜", ""))
        if d != cur:
            cur = d
            parts.append(day_html(d, per_day[d], load_run(runs_dir, d), repo_url))
        is_new = bool(latest_run) and str(a.get("수집일", "")) == latest_run
        new_count += is_new
        parts.append(item_html(a, is_new))
    feed = "\n".join(parts) if parts else '<div class="nomatch">아직 수집된 항목이 없습니다.</div>'

    latest_iso = day_counts[0][0] if day_counts else ""
    latest_items = [a for a in recent if str(a.get("날짜", "")) == latest_iso]
    brief = brief_html(latest_iso, latest_items, load_run(runs_dir, latest_iso) if latest_iso else None, repo_url)

    out = TEMPLATE.read_text(encoding="utf-8")
    for k, v in {
        "{{갱신일}}": fmt_long(today),
        "{{총건수}}": str(len(recent)),
        "{{리포URL}}": attr(repo_url),
        "<!--BRIEF-->": brief,
        "<!--DATES-->": dates_html(day_counts),
        "<!--SECS-->": secs_html(recent),
        "<!--FEED-->": feed,
    }.items():
        out = out.replace(k, v)

    out_path = Path(args.output_html)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out, encoding="utf-8")
    print(f"RENDERED total={len(recent)} new={new_count} window={start_iso}~{today.isoformat()}")


if __name__ == "__main__":
    main()
