#!/usr/bin/env python3
"""누적 항목 JSON으로 docs/index.html(트렌드 피드)을 생성한다.

Usage:
  python build_site.py <items_json> <output_html> [--days 30]

- 최근 N일(기본 30일, KST 오늘 포함) 항목만 렌더링한다.
- 날짜별 구분선 아래 항목 행이 이어지는 피드. 가장 최근 `수집일` 항목에는 NEW 표시.
- 항목 필드: 섹션, 태그, 제목, 제공자, 출처, 날짜, 링크, 관련링크(선택), 이미지(선택),
  한줄정리, 왜중요, 써보기(선택), 세부(화면에는 표시하지 않음), 수집일
"""

from __future__ import annotations

import argparse
import html
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE = SCRIPT_DIR.parent / "templates" / "dashboard.html"
KST = timezone(timedelta(hours=9))
WEEKDAYS = "월화수목금토일"
SECTIONS = ["모델·API", "도구·에이전트", "스킬·MCP", "기법·연구"]
SEC_SLUG = {"모델·API": "model", "도구·에이전트": "tool", "스킬·MCP": "mcp", "기법·연구": "research"}
SEC_ORDER = {s: i for i, s in enumerate(SECTIONS)}
TAGS = {"신규출시", "업데이트", "오픈소스", "실전팁"}


def esc(v) -> str:
    return html.escape(str(v or "").strip())


def attr(v) -> str:
    return html.escape(str(v or "").strip(), quote=True)


def fmt_long(d: date) -> str:
    return f"{d.year}년 {d.month}월 {d.day}일 ({WEEKDAYS[d.weekday()]})"


def tag_of(a: dict) -> str:
    t = str(a.get("태그", "")).strip()
    return t if t in TAGS else "업데이트"


def sec_of(a: dict) -> str:
    s = str(a.get("섹션", "")).strip()
    return s if s in SEC_SLUG else SECTIONS[-1]


def search_text(a: dict) -> str:
    parts = [a.get(k, "") for k in ("제목", "제공자", "출처", "한줄정리", "왜중요", "써보기")]
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
    sec, slug, tag = sec_of(a), SEC_SLUG[sec_of(a)], tag_of(a)
    url = str(a.get("링크", "")).strip()
    href = attr(url) if url else "#"
    img = str(a.get("이미지", "")).strip()
    thumb = (
        f'<img class="thumb" src="{attr(img)}" alt="" loading="lazy" referrerpolicy="no-referrer" />'
        if img else ""
    )
    meta = [
        f'<span class="sec sec-{slug}">{esc(sec)}</span>',
        f'<span class="tag tag-{tag}">{tag}</span>',
    ]
    if a.get("제공자"):
        meta.append(f'<span class="prov">{esc(a["제공자"])}</span>')
    if is_new:
        meta.insert(0, '<span class="new">NEW</span>')

    why = esc(a.get("왜중요"))
    why_html = f'<p class="why">{why}</p>' if why else ""
    try_code = str(a.get("써보기", "")).strip()
    try_html = (
        f'<details class="try"><summary>써보기</summary><pre><code>{esc(try_code)}</code></pre></details>'
        if try_code else ""
    )
    foot_src = esc(a.get("출처"))
    rel = links_html(a.get("관련링크"))
    return (
        f'<article class="item{"" if img else " no-img"}" data-sec="{attr(sec)}" data-tag="{tag}" data-text="{search_text(a)}">'
        f'<div class="meta">{" ".join(meta)}</div>'
        f'<h3><a href="{href}" target="_blank" rel="noreferrer">{esc(a.get("제목", "제목 미상"))}</a></h3>'
        f'<p class="one">{esc(a.get("한줄정리") or "원문 미확보")}</p>'
        f"{why_html}{try_html}"
        f'<div class="foot"><span class="src">{foot_src}</span>{rel}</div>'
        f"{thumb}</article>"
    )


def day_html(iso: str, n: int) -> str:
    try:
        d = date.fromisoformat(iso)
        label = f"{d.month}월 {d.day}일 ({WEEKDAYS[d.weekday()]})"
    except ValueError:
        label = esc(iso)
    return f'<div class="day"><h2>{label}</h2><span class="n">{n}건</span><span class="line"></span></div>'


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("items_json")
    ap.add_argument("output_html")
    ap.add_argument("--days", type=int, default=30)
    args = ap.parse_args()

    with open(args.items_json, encoding="utf-8-sig") as fh:
        items = json.load(fh)

    today = datetime.now(KST).date()
    start_iso = (today - timedelta(days=args.days - 1)).isoformat()
    recent = [a for a in items if str(a.get("날짜", "")) >= start_iso]
    recent.sort(key=lambda a: (a.get("제공자", ""), a.get("제목", "")))
    recent.sort(key=lambda a: SEC_ORDER.get(sec_of(a), len(SECTIONS)))
    recent.sort(key=lambda a: a.get("날짜", ""), reverse=True)

    latest_run = max((str(a.get("수집일", "")) for a in recent), default="")
    per_day: dict[str, int] = {}
    for a in recent:
        per_day[str(a.get("날짜", ""))] = per_day.get(str(a.get("날짜", "")), 0) + 1

    parts: list[str] = []
    cur = None
    new_count = 0
    for a in recent:
        d = str(a.get("날짜", ""))
        if d != cur:
            cur = d
            parts.append(day_html(d, per_day[d]))
        is_new = bool(latest_run) and str(a.get("수집일", "")) == latest_run
        new_count += is_new
        parts.append(item_html(a, is_new))
    feed = "\n".join(parts) if parts else '<div class="empty">아직 수집된 항목이 없습니다.</div>'

    sec_counts = {s: sum(1 for a in recent if sec_of(a) == s) for s in SECTIONS}
    sec_summary = " · ".join(f"{s} {n}" for s, n in sec_counts.items())

    out = TEMPLATE.read_text(encoding="utf-8")
    for k, v in {
        "{{갱신일}}": fmt_long(today),
        "{{총건수}}": str(len(recent)),
        "{{섹션요약}}": sec_summary,
        "<!--FEED-->": feed,
    }.items():
        out = out.replace(k, v)

    out_path = Path(args.output_html)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out, encoding="utf-8")
    print(f"RENDERED total={len(recent)} new={new_count} window={start_iso}~{today.isoformat()}")


if __name__ == "__main__":
    main()
