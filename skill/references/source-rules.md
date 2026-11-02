# Source Rules

수집은 `공식 출처 순회 -> 커뮤니티 시드 -> 보조 검색 -> 원본 검증 -> 정리 고정`으로 고정한다. 목표는 많이 모으는 것이 아니라, **사용자가 오늘 직접 써볼 수 있는 변화**를 빠뜨리지 않으면서 매일 비슷한 품질의 묶음을 만드는 것이다.

## 기간 고정

- 수집 대상: KST 기준 **어제 하루** (`YYYY-MM-DD` 1일). 출처가 미국 시간대인 경우 현지 날짜 기준.
- 주말이라 조용하면 그대로 적게 싣는다. 기간을 늘리지 않는다.

## 분량 기준

- 섹션당 0~4건, 하루 총 3~12건이 보통이다. 건수 목표는 두지 않는다.
- 기준을 넘는 항목은 모두 싣는다. 상한을 맞추려고 좋은 항목을 버리지 않는다.
- 기준 미달 항목을 건수 채우기용으로 넣지 않는다. 0건인 섹션도 정상이다.

## 포함 기준 (모든 섹션 공통)

아래 셋을 모두 만족해야 한다.

1. **실체가 있다**: 모델·API 기능·도구 릴리스·레포·사양·구체적 기법 중 하나다. "AI가 바꿀 미래" 류의 의견·전망·업계 동향 요약이 아니다.
2. **써볼 수 있다**: API 호출, CLI 설치, 설정 변경, 레포 clone, 프롬프트 패턴 적용 중 하나로 사용자가 직접 해볼 수 있다. 내부 전용·초청 전용·발표만 되고 접근 불가면 `왜중요`에 그 사실을 적고, 영향이 큰 경우에만 포함한다.
3. **어제 나왔다**: 공식 발표일·릴리스 날짜·레포 공개일·글 발행일이 `TARGET`이다.

## 섹션 정의와 출처

### 1. 모델·API

새 모델, 모델 버전 업데이트, API 신기능(툴 사용·캐싱·배치·파일·구조화 출력·컴퓨터 사용 등), 가격·컨텍스트·한도 변경, 모델 제공 종료.

필수 출처:

- `anthropic.com/news`, `docs.anthropic.com` 릴리스 노트(`/en/release-notes/api`, `/en/release-notes/overview`)
- `openai.com/news`, `platform.openai.com/docs/changelog`
- `blog.google/technology/ai`, `deepmind.google/discover/blog`, `ai.google.dev/gemini-api/docs/changelog`
- `ai.meta.com/blog`
- `mistral.ai/news`
- `huggingface.co/blog`, Hugging Face 트렌딩 모델(`huggingface.co/models?sort=trending`)
- `x.ai/news`
- 오픈 모델 공개: Qwen, DeepSeek, Kimi(Moonshot), GLM(Zhipu), Llama 계열 공식 블로그·레포

보조 검색: `new model release {TARGET}`, `model card {TARGET}`, `API changelog {TARGET}`, `open weights release {TARGET}`, `{제공자명} announces model`

### 2. 도구·에이전트

코딩 에이전트·IDE(Claude Code, OpenAI Codex, Cursor, Gemini CLI, GitHub Copilot, Windsurf, Cline, Roo Code, Aider, Zed, VS Code AI 기능), 에이전트 프레임워크·SDK(Claude Agent SDK, OpenAI Agents SDK, LangGraph, Google ADK 등), 에이전트 런타임·배포·관측 도구, 데스크톱·브라우저 에이전트.

필수 출처:

- Claude Code: `github.com/anthropics/claude-code/blob/main/CHANGELOG.md`, `code.claude.com/docs` 체인지로그
- OpenAI Codex: `github.com/openai/codex/releases`, `developers.openai.com/codex/changelog`
- Cursor: `cursor.com/changelog`
- Gemini CLI: `github.com/google-gemini/gemini-cli/releases`
- GitHub Copilot: `github.blog/changelog` (Copilot 항목)
- Cline / Roo Code / Aider / Zed: 각 GitHub 릴리스
- VS Code: `code.visualstudio.com/updates` (월 1회, AI 항목)
- 프레임워크: `github.com/anthropics/claude-agent-sdk-*`, `github.com/openai/openai-agents-python` 릴리스, LangChain 블로그

보조 검색: `coding agent release {TARGET}`, `agent SDK release {TARGET}`, `CLI changelog {TARGET}`, `{도구명} v` + 릴리스

패치 릴리스 처리: 같은 도구의 연속 패치(x.y.1 → x.y.2)는 사용자가 체감할 변경(새 명령·설정·모델 지원·동작 변경)이 있을 때만 1건으로 싣는다. 버그 수정만이면 제외한다.

### 3. 스킬·MCP

스킬(Agent Skills, SKILL.md 형식), MCP 서버·클라이언트·레지스트리, Claude Code 플러그인·훅, MCP 사양 변경, 주요 서비스의 공식 MCP 서버 출시, 커넥터.

필수 출처:

- `github.com/anthropics/skills`, 스킬 사양 문서
- `github.com/modelcontextprotocol/servers`, `github.com/modelcontextprotocol/modelcontextprotocol` (사양·블로그 `blog.modelcontextprotocol.io`), `registry.modelcontextprotocol.io`
- MCP 디렉터리: `github.com/punkpeye/awesome-mcp-servers`, `smithery.ai`, `glama.ai/mcp/servers`, `mcp.so`
- Claude Code 플러그인·마켓플레이스 관련 공식 문서·레포
- 주요 서비스(GitHub, Notion, Slack, Figma, Stripe, Cloudflare, AWS, Google 등)의 공식 MCP 서버 발표

보조 검색: `MCP server release {TARGET}`, `official MCP server {TARGET}`, `Agent Skills {TARGET}`, `Claude Code plugin {TARGET}`, `SKILL.md`

커뮤니티 레포 포함 기준: `TARGET`에 공개됐거나 HN/Reddit에서 처음 주목받은 레포만. 스타 수보다 **용도가 명확하고 README에 설치·설정이 있는지**를 본다. 공식 서버 복제·토이 수준은 제외.

### 4. 기법·연구

프롬프팅·컨텍스트 엔지니어링·에이전트 설계 패턴·평가 방법·비용 절감 기법, 실무에 바로 닿는 연구 결과, 깊이 있는 비교·벤치마크 글, 공식 엔지니어링 블로그의 사례.

필수 출처:

- 공식 엔지니어링 블로그: `anthropic.com/engineering`, `openai.com/index` 연구 항목, `developers.googleblog.com`
- 블로거·뉴스레터: `simonwillison.net`, `latent.space`, `interconnects.ai`, `www.oneusefulthing.org`, `newsletter.pragmaticengineer.com` AI 항목
- 커뮤니티: `news.ycombinator.com` 프론트 페이지, `reddit.com/r/ClaudeAI`, `reddit.com/r/LocalLLaMA`, `reddit.com/r/MachineLearning`
- 논문: `arxiv.org` cs.CL / cs.AI 중 **코드·데모가 공개되고 실무 적용 방법이 명확한 것**만. 순수 이론·벤치마크 수치 경쟁만인 논문은 제외

보조 검색: `prompt engineering {TARGET}`, `context engineering`, `agent design pattern`, `LLM evaluation practical`, `token cost reduction`

이 섹션은 `실전팁` 태그가 기본이다. 다른 섹션에 해당하는 발표를 다룬 커뮤니티 글은 여기가 아니라 해당 섹션에 **원본 URL**로 싣는다.

## 태그 기준

- `신규출시`: 처음 나온 모델·제품·레포·서버
- `업데이트`: 기존 것의 기능 추가·변경·가격 변경·사양 개정
- `오픈소스`: 가중치·코드 공개가 핵심인 항목 (신규든 업데이트든)
- `실전팁`: 사용법·패턴·비교·사례 글

## 제외 규칙

- 자금 조달·인수·인사·실적·소송 등 비즈니스 뉴스 (제품 변화가 핵심이 아니면)
- 전망·의견·칼럼, "AI 트렌드 10가지" 류의 요약·리스트 글
- 마케팅 랜딩 페이지, 웨이트리스트만 열린 발표 (영향이 매우 큰 경우 예외)
- 특정 도구 추천·순위 글, 어필리에이트성 비교 글
- 소비자용 챗봇 UI의 사소한 변경 (API·개발자 도구와 무관한 것)
- 원본 확인이 안 되는 재배포 글, 번역 재게시
- 날짜가 범위를 벗어난 항목, 같은 발표의 중복
- 유튜브·개인 블로그 플랫폼(`blog.naver.com`, `tistory.com`, `brunch.co.kr`, `velog.io`) 글. 단, 그 글이 가리키는 원본은 후보가 된다
- `medium.com`은 원칙 제외. 공식 조직 퍼블리케이션(예: 벤더 엔지니어링 블로그가 medium에 있는 경우)만 허용

## 중복·대표 선택 규칙

같은 발표를 여러 곳이 다룰 때 아래 순서로 1건을 고른다.

1. 제공자 공식 발표·체인지로그·릴리스 페이지
2. 공식 문서 페이지
3. 공식 레포
4. 1차 분석 글(Simon Willison 등 직접 테스트한 글)
5. 매체 기사·커뮤니티 글

선택되지 않은 URL 중 유용한 것(문서·레포)은 `관련링크`로 붙인다.

## 동률 해소 규칙

여러 항목이 비슷하면 아래 순서로 우선한다.

1. 직접 써볼 수 있는 정도 (공개 API/다운로드 가능 > 베타 신청 > 발표만)
2. 영향 범위 (여러 도구·워크플로에 걸침 > 한 도구의 한 기능)
3. 신규성 (누적 데이터에 같은 제품의 발표가 최근 14일 내 없음)
4. 출처 신뢰도 (공식 > 1차 분석 > 매체)
5. 제목 명확성

## 정렬 규칙

- 피드는 `날짜 desc -> 섹션 순서(모델·API, 도구·에이전트, 스킬·MCP, 기법·연구) -> 제공자 asc -> 제목 asc`
- 최종 JSON은 `append_items.py`가 정렬을 맡는다.
