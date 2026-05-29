# 디자인 시안 선정 결과 (CHOICE)

> Claude Design 핸드오프 → 확정 조합 기록. DECISIONS G4 [확정] 참조.

## 확정 조합 (2026-05-30, 사용자 승인)

| 변형 축 | 확정값 | 근거 |
|---------|--------|------|
| 전체 톤 | **우드** (따뜻한 강조) | 미니멀+따뜻함 컨셉 1순위 |
| 카드 스타일 | **그림자** (shadow) | 오늘의집풍 입체·따뜻 |
| 밀도 | **미니멀** | 모바일 가독성·컨셉 정합 |

→ 변형 토글(`data-tone`/`data-card`/`data-density`)은 코드에서 제거하고 위 값만 확정 적용.

## 핸드오프 출처

- 도구: claude.ai/design "클로드 코드에게 인계"
- URL: `api.anthropic.com/v1/design/h/DuL14k3ymgHxfyCshq9EhQ`
- 수신: WebFetch → 4MB gzip → `docs/design_drafts/honsalim/` (README·chats·project·screenshots 전체)

## 생성 산출물 (코드)

- 템플릿: `templates/{base,home,scenario_list,article,persona_hub,about}.html` + `partials/{header,footer}.html` + `_macros/components.html`
- CSS: `static/css/{tokens,components,pages}.css`
- JS: `static/js/hub-filter.js` (허브 필터 점진적 향상)
- 미리보기 빌드: `scripts/preview_build.py` (목업 데이터, 19페이지)

## 원본 대비 변경 (정책 정합)

- About "이미지 출처 정책": "직접 촬영" → "AI 생성+AI 표기, 제품은 공식 위젯" (DECISIONS L2)
- 사업자 정보: 운영자 "혼살다", 이메일 dugihappyending@gmail.com, 사업자번호·주소 "등록 진행 중" (DECISIONS M2)
- 제휴 링크 `rel="sponsored nofollow"`, React→정적 `<a href>`

## 차기 작업

- 정식 빌더 `src/builder/renderer.py` (DB 연동·실제 콘텐츠)
- meta/OG·JSON-LD 매크로(`_macros/{meta,schema,image}.html`), Person Schema(M2-1~M2-7)
- Pretendard self-host + preload, critical CSS 인라인, `main.{hash}.css` 단일화
- sitemap.xml·feed.xml·404.html 템플릿
