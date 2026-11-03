# ai-trend-daily

AI 기술 동향 일간 피드. 새로 나온 모델·API, 코딩 에이전트·도구 업데이트, 스킬·MCP 서버, 실용적인 기법 중 **직접 써볼 수 있는 것**을 매일 새벽 3시(KST) 클라우드 루틴이 전날분으로 수집해 누적하고 피드 페이지를 재생성한다.

- 피드: https://g2e-yunseonghun.github.io/ai-trend-daily/
- 수집·작성 절차: `skill/SKILL.md`
- 출처·포함/제외 규칙: `skill/references/source-rules.md`
- 누적 데이터: `data/items.json`
- 출력: `docs/index.html` (최근 30일만 표시, GitHub Pages가 서빙)

## 섹션

| 섹션 | 다루는 것 |
|---|---|
| 모델·API | 새 모델, 모델 업데이트, API 신기능(툴·캐싱·배치·파일 등), 가격·한도 변경 |
| 도구·에이전트 | Claude Code·Codex·Cursor·Gemini CLI·Copilot 등 코딩 에이전트/IDE, 에이전트 프레임워크 |
| 스킬·MCP | 스킬, MCP 서버·클라이언트, 플러그인, 프로토콜 사양 변경 |
| 기법·연구 | 프롬프팅·컨텍스트 엔지니어링·에이전트 설계 패턴, 실무에 바로 닿는 연구 결과 |

## 구조

```
skill/
  SKILL.md                    일간 수집 절차
  references/source-rules.md  출처 목록·포함/제외 기준·중복 처리 규칙
  scripts/extract.py          URL → 본문·발행일·og:image (GitHub URL은 API로 릴리스 날짜·설명 보강)
  scripts/append_items.py     새 항목을 누적 파일에 URL 중복 대조 후 병합, 수집일 기록
  scripts/build_site.py       최근 30일 항목 → docs/index.html
  templates/dashboard.html    피드 템플릿 (섹션·태그 필터, 검색)
data/items.json               누적 항목
docs/index.html               피드
```

## 수동 실행

```bash
pip install trafilatura requests playwright && playwright install chromium
echo '["https://..."]' | python skill/scripts/extract.py > _work/extracted.json
python skill/scripts/append_items.py _work/new_items.json data/items.json
python skill/scripts/build_site.py data/items.json docs/index.html
```
