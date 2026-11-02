#!/usr/bin/env python3
"""새 항목을 누적 items.json에 병합한다.

Usage:
  python append_items.py <new_items_json> <items_json_path>

<new_items_json>: 항목 객체 배열. 각 객체는 최소 "섹션", "태그", "제목", "링크", "날짜"를 가진다.
<items_json_path>: 누적 파일. 없으면 빈 배열로 시작한다.

URL(fragment·trailing slash 제거, 소문자)이 같은 항목은 건너뛴다.
추가된 항목에는 "수집일"(KST 오늘)을 찍는다. build_site.py가 이 값으로 NEW 표시를 만든다.
stdout 마지막 줄에 "ADDED:<n> SKIPPED:<m> TOTAL:<t>"를 출력한다.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

KST = timezone(timedelta(hours=9))
SECTIONS = ["모델·API", "도구·에이전트", "스킬·MCP", "기법·연구"]
TAGS = {"신규출시", "업데이트", "오픈소스", "실전팁"}
DATE_BASES = {"릴리스일", "공개일", "발행일", "발표일", "주목일"}
TITLE_MAX = 60
SEC_ORDER = {s: i for i, s in enumerate(SECTIONS)}


def normalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    path = parts.path.rstrip("/")
    # 릴리스 태그·문서 앵커 등 쿼리에 식별자가 있는 경우가 있어 쿼리는 유지한다.
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, parts.query, ""))


def sort_key(a: dict):
    return (
        a.get("날짜", ""),
        -SEC_ORDER.get(a.get("섹션", ""), len(SECTIONS)),
        a.get("제공자", ""),
        a.get("제목", ""),
    )


def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    return data if isinstance(data, list) else []


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python append_items.py <new_items_json> <items_json_path>")
        sys.exit(1)

    new_path = Path(sys.argv[1])
    store_path = Path(sys.argv[2])

    new_items = _load(new_path)
    existing = _load(store_path)
    seen = {normalize_url(a.get("링크", "")) for a in existing if a.get("링크")}
    today = datetime.now(KST).date().isoformat()

    added = skipped = 0
    for item in new_items:
        link = item.get("링크", "")
        key = normalize_url(link) if link else ""
        if not key or key in seen:
            skipped += 1
            continue
        if item.get("섹션") not in SECTIONS:
            raise SystemExit(f"섹션 값이 잘못됨: {item.get('섹션')!r} ({link})")
        if item.get("태그") not in TAGS:
            raise SystemExit(f"태그 값이 잘못됨: {item.get('태그')!r} ({link})")
        basis = item.get("날짜근거")
        if basis and basis not in DATE_BASES:
            raise SystemExit(f"날짜근거 값이 잘못됨: {basis!r} ({link}) — {sorted(DATE_BASES)} 중 하나")
        if len(str(item.get("제목", ""))) > TITLE_MAX:
            print(f"WARN 제목 {len(str(item['제목']))}자 > {TITLE_MAX}자: {item['제목']}")
        item.pop("원문", None)
        item["수집일"] = today
        existing.append(item)
        seen.add(key)
        added += 1

    hl_per_day: dict[str, int] = {}
    for a in existing:
        if a.get("하이라이트"):
            hl_per_day[a.get("날짜", "")] = hl_per_day.get(a.get("날짜", ""), 0) + 1
    for d, n in hl_per_day.items():
        if n > 1:
            print(f"WARN {d} 하이라이트 {n}건 — 하루 1건이 원칙")

    # 날짜 desc → 섹션 순서 → 제공자 asc → 제목 asc
    existing.sort(key=lambda a: (a.get("제공자", ""), a.get("제목", "")))
    existing.sort(key=lambda a: SEC_ORDER.get(a.get("섹션", ""), len(SECTIONS)))
    existing.sort(key=lambda a: a.get("날짜", ""), reverse=True)

    store_path.parent.mkdir(parents=True, exist_ok=True)
    store_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"ADDED:{added} SKIPPED:{skipped} TOTAL:{len(existing)}")


if __name__ == "__main__":
    main()
