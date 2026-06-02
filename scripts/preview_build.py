# mypy: ignore-errors
# (개발용 목업 빌드 스크립트 — 정식 타입검사 대상은 src/builder/renderer.py)
"""혼살림 — 공개 사이트 5종 미리보기 빌드.

Claude Design 핸드오프(우드/그림자/미니멀)를 Jinja2 템플릿으로 이식한 결과를
실제 HTML로 렌더해 build/preview/ 아래로 출력한다. 페이지 간 클릭 이동을 위해
절대경로(/static, /articles/<id>/)를 쓰며, 로컬 HTTP 서버로 확인한다.

    python scripts/preview_build.py
    python -m http.server 8787 --directory build/preview
    → http://localhost:8787/ 접속

정식 빌드 파이프라인(builder.renderer·asset hash·critical CSS·DB 연동)은 Phase 3 별도 작업.
콘텐츠는 디자인 data.jsx 기반 목업이며, 실제 발행 콘텐츠가 아니다.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
OUT = ROOT / "build" / "preview"

PERSONA_ICON = {"jachi": "key", "jaetaek": "laptop", "jeongchak": "plant"}
SEASON_ICON = {"봄": "spring", "여름": "summer", "가을": "fall", "겨울": "winter"}


# ---- 페르소나 3종 (디자인 data.jsx 전체 필드) -------------------------------

PERSONAS = [
    {
        "id": "jachi",
        "name": "자취 시작",
        "line": "처음 독립하는 1인 가구를 위한 첫 살림 가이드",
        "desc": "원룸·오피스텔에 막 들어온 분. 무엇부터 사야 할지, 한정된 예산을 어떻게 쪼갤지 고민이 가장 큰 단계입니다.",
        "bullets": [
            "이번 달에 처음 독립했거나 곧 이사 예정인 분",
            "가구·가전이 거의 없어 0부터 채워야 하는 분",
            "30~50만 원 안에서 필수만 갖추고 싶은 분",
        ],
        "avgBudget": "32만 원",
        "keywords": ["원룸 풀세팅", "자취 필수템", "좁은 주방", "1인 밥솥"],
        "peak": "2~3월 · 8~9월 (이사 시즌)",
        "img": "var(--wood-1)",
    },
    {
        "id": "jaetaek",
        "name": "재택·홈오피스",
        "line": "집에서 일하는 시간이 긴 분을 위한 환경 가이드",
        "desc": '하루 대부분을 집에서 보내며 일하는 분. 책상·의자·조명 같은 "오래 쓰는 환경"에 투자가치가 가장 높은 단계입니다.',
        "bullets": [
            "재택근무·프리랜서로 집에서 일하는 시간이 긴 분",
            "허리·목·눈 피로 등 작업 환경 개선이 필요한 분",
            "한 번 살 때 오래 쓸 제품을 찾는 분",
        ],
        "avgBudget": "58만 원",
        "keywords": ["재택 책상셋업", "인체공학 의자", "모니터암", "간접조명"],
        "peak": "연중 고른 편 · 1월 (연초 환경개선)",
        "img": "var(--wood-4)",
    },
    {
        "id": "jeongchak",
        "name": "정착·오래 살 집",
        "line": "한 집에 오래 머물며 살림을 갖춰가는 분을 위한 가이드",
        "desc": "이사를 자주 다니지 않고 정착해 사는 분. 가전·수납·생활 동선을 제대로 갖춰 살림의 질을 높이는 단계입니다.",
        "bullets": [
            "같은 집에 2년 이상 거주 예정인 분",
            "필수템은 갖췄고 생활의 질을 높이고 싶은 분",
            "가전·수납 등 비교적 큰 지출을 계획하는 분",
        ],
        "avgBudget": "81만 원",
        "keywords": ["1인 가전", "빨래건조", "수납정리", "환절기 이불"],
        "peak": "11~1월 (겨울 난방·보온)",
        "img": "var(--wood-2)",
    },
]
for _p in PERSONAS:
    _p["icon"] = PERSONA_ICON[_p["id"]]
    _p["url"] = f"/personas/{_p['id']}/"
PERSONA_NAME = {p["id"]: p["name"] for p in PERSONAS}


# ---- 시나리오 12종 ----------------------------------------------------------

SCENARIOS = [
    {
        "id": "s1",
        "title": "원룸 첫 자취 풀세팅",
        "persona": "jachi",
        "season": "봄",
        "budget": "30만 원대",
        "budget_tier": "mid",
        "count": 11,
        "hot": True,
        "desc": "이불·주방·청소·수납까지 — 처음 독립할 때 진짜 필요한 것만 골랐습니다.",
        "img": "var(--wood-1)",
        "cap": "원룸 거실 풀세팅",
    },
    {
        "id": "s2",
        "title": "재택근무 책상 셋업",
        "persona": "jaetaek",
        "season": "사계절",
        "budget": "50만 원대",
        "budget_tier": "high",
        "count": 9,
        "hot": True,
        "desc": "오래 앉아도 덜 피곤한 책상·의자·조명 조합. 한 번에 갖추는 작업 환경.",
        "img": "var(--wood-4)",
        "cap": "홈오피스 책상",
    },
    {
        "id": "s3",
        "title": "좁은 주방 살림 시작",
        "persona": "jachi",
        "season": "가을",
        "budget": "10만 원대",
        "budget_tier": "low",
        "count": 8,
        "hot": True,
        "desc": "1구 인덕션 한 칸에서도 요리가 되는 최소 주방 살림 구성.",
        "img": "var(--wood-3)",
        "cap": "미니 주방",
    },
    {
        "id": "s4",
        "title": "1인 가구 가전 정착 패키지",
        "persona": "jeongchak",
        "season": "겨울",
        "budget": "80만 원대",
        "budget_tier": "high",
        "count": 10,
        "hot": True,
        "desc": "오래 쓸 냉장고·세탁기·청소기. 1인 가구 사이즈로 추린 가전 묶음.",
        "img": "var(--wood-2)",
        "cap": "1인 가전",
    },
    {
        "id": "s5",
        "title": "환절기 빨래·건조 해결",
        "persona": "jeongchak",
        "season": "환절기",
        "budget": "20만 원대",
        "budget_tier": "mid",
        "count": 7,
        "hot": True,
        "desc": "실내 건조 냄새 없이. 제습기·건조대·세탁세제까지 한 번에.",
        "img": "var(--wood-1)",
        "cap": "베란다 건조",
    },
    {
        "id": "s6",
        "title": "작은 방 수면·조명 환경",
        "persona": "jachi",
        "season": "여름",
        "budget": "20만 원대",
        "budget_tier": "mid",
        "count": 8,
        "hot": True,
        "desc": "잘 자는 게 먼저. 암막·간접조명·매트리스 토퍼로 만드는 수면 공간.",
        "img": "var(--wood-4)",
        "cap": "침실 조명",
    },
    {
        "id": "s7",
        "title": "여름 제습·냉방 최소 구성",
        "persona": "jeongchak",
        "season": "여름",
        "budget": "30만 원대",
        "budget_tier": "mid",
        "count": 6,
        "hot": False,
        "desc": "에어컨 없이 버티는 원룸을 위한 서큘레이터·제습 조합.",
        "img": "var(--wood-3)",
        "cap": "여름 냉방",
    },
    {
        "id": "s8",
        "title": "혼밥 주방가전 3종",
        "persona": "jachi",
        "season": "사계절",
        "budget": "20만 원대",
        "budget_tier": "mid",
        "count": 5,
        "hot": False,
        "desc": "에어프라이어·미니밥솥·전기포트. 혼밥을 편하게 만드는 조합.",
        "img": "var(--wood-1)",
        "cap": "주방 가전",
    },
    {
        "id": "s9",
        "title": "재택 화상회의 환경",
        "persona": "jaetaek",
        "season": "사계절",
        "budget": "20만 원대",
        "budget_tier": "mid",
        "count": 7,
        "hot": False,
        "desc": "웹캠·마이크·링라이트 — 얼굴이 또렷하게 보이는 회의 셋업.",
        "img": "var(--wood-4)",
        "cap": "화상회의",
    },
    {
        "id": "s10",
        "title": "좁은 집 수납 정리",
        "persona": "jeongchak",
        "season": "봄",
        "budget": "10만 원대",
        "budget_tier": "low",
        "count": 9,
        "hot": False,
        "desc": "버리지 않고도 넓어 보이게. 1인 가구 수납·정리 기본템.",
        "img": "var(--wood-2)",
        "cap": "수납 정리",
    },
    {
        "id": "s11",
        "title": "겨울 난방·보온 살림",
        "persona": "jeongchak",
        "season": "겨울",
        "budget": "20만 원대",
        "budget_tier": "mid",
        "count": 8,
        "hot": False,
        "desc": "난방비 아끼며 따뜻하게. 전기요·온수매트·문풍지 구성.",
        "img": "var(--wood-1)",
        "cap": "겨울 보온",
    },
    {
        "id": "s12",
        "title": "입주 첫날 생필품 키트",
        "persona": "jachi",
        "season": "사계절",
        "budget": "10만 원대",
        "budget_tier": "low",
        "count": 10,
        "hot": False,
        "desc": "이사 당일 바로 필요한 휴지·수건·청소도구·기본 공구 모음.",
        "img": "var(--wood-3)",
        "cap": "입주 키트",
    },
]
for _s in SCENARIOS:
    _s["persona_name"] = PERSONA_NAME.get(_s["persona"], "")
    _s["persona_icon"] = PERSONA_ICON.get(_s["persona"], "")
    _s["season_icon"] = SEASON_ICON.get(_s["season"], "")
    _s["url"] = f"/articles/{_s['id']}/"


# ---- 시즌 캘린더 (홈) -------------------------------------------------------

SEASONS = [
    {
        "id": "spring",
        "icon": "spring",
        "name": "봄",
        "sub": "이사·풀세팅",
        "months": "2~4월",
        "desc": "이사 성수기. 원룸 첫 세팅과 수납 정리 수요가 가장 높은 시기.",
        "img": "var(--wood-3)",
    },
    {
        "id": "summer",
        "icon": "summer",
        "name": "여름",
        "sub": "제습·수면",
        "months": "5~8월",
        "desc": "습기·열대야 대응. 제습기·서큘레이터·암막·쿨매트 중심.",
        "img": "var(--wood-1)",
    },
    {
        "id": "fall",
        "icon": "fall",
        "name": "가을",
        "sub": "주방·정리",
        "months": "9~10월",
        "desc": "환절기 정리와 주방 살림 보강. 빨래 건조 고민이 시작되는 시기.",
        "img": "var(--wood-2)",
    },
    {
        "id": "winter",
        "icon": "winter",
        "name": "겨울",
        "sub": "난방·보온",
        "months": "11~1월",
        "desc": "난방비·보온이 핵심. 전기요·온수매트·가전 정착 수요 급증.",
        "img": "var(--wood-4)",
    },
]
for _s in SEASONS:
    _s["url"] = f"/scenarios/?season={_s['name']}"


# ---- 허브 필터 옵션 ---------------------------------------------------------

BUDGET_FILTERS = [
    {"id": "low", "label": "10만 원대"},
    {"id": "mid", "label": "20~30만 원대"},
    {"id": "high", "label": "50만 원 이상"},
]
SEASON_FILTERS = [
    {"value": s, "icon": SEASON_ICON.get(s, "")}
    for s in ["봄", "여름", "가을", "겨울", "사계절", "환절기"]
]


# ---- 상세페이지 목업 (원룸 첫 자취 풀세팅 기준) -----------------------------

PRODUCTS = [
    {
        "name": "1인용 경량 차렵이불 세트",
        "cat": "침구",
        "price": "3.9만 원",
        "tag": "필수",
        "why": "사계절 쓰기 좋은 무난한 두께. 세탁 후 빨리 마름.",
        "img": "var(--wood-3)",
    },
    {
        "name": "미니 6인용 전기밥솥",
        "cat": "주방가전",
        "price": "4.5만 원",
        "tag": "필수",
        "why": "혼밥 양에 딱. 보온 오래 가고 내솥 코팅이 무난.",
        "img": "var(--wood-1)",
    },
    {
        "name": "2구 인덕션 (이동형)",
        "cat": "주방가전",
        "price": "5.9만 원",
        "tag": "필수",
        "why": "가스 없는 원룸 필수. 화구 2개로 동시 조리 가능.",
        "img": "var(--wood-4)",
    },
    {
        "name": "슬림 4단 수납 선반",
        "cat": "수납",
        "price": "2.8만 원",
        "tag": "추천",
        "why": "폭 30cm로 좁은 틈에 쏙. 주방·욕실 어디든.",
        "img": "var(--wood-2)",
    },
    {
        "name": "무선 핸디 스틱청소기",
        "cat": "청소",
        "price": "8.9만 원",
        "tag": "추천",
        "why": "원룸 청소엔 이 정도면 충분. 가볍고 충전 빠름.",
        "img": "var(--wood-1)",
    },
    {
        "name": "접이식 빨래 건조대",
        "cat": "세탁",
        "price": "2.3만 원",
        "tag": "추천",
        "why": "안 쓸 땐 납작하게. 1인 빨래량에 맞는 크기.",
        "img": "var(--wood-3)",
    },
    {
        "name": "LED 스탠드 (밝기조절)",
        "cat": "조명",
        "price": "3.2만 원",
        "tag": "선택",
        "why": "눈 편한 색온도. 책상·침대 겸용으로 활용도 높음.",
        "img": "var(--wood-4)",
    },
    {
        "name": "욕실 5종 기본세트",
        "cat": "생활",
        "price": "1.9만 원",
        "tag": "선택",
        "why": "수건걸이·칫솔꽂이 등 한 번에. 설치 간단.",
        "img": "var(--wood-2)",
    },
]

BUDGET_TABLE = {
    "total": "35.4만 원",
    "rows": [
        {"cat": "침구·수면", "amt": "3.9만 원", "pct": 11},
        {"cat": "주방가전", "amt": "10.4만 원", "pct": 29},
        {"cat": "청소·세탁", "amt": "11.2만 원", "pct": 32},
        {"cat": "수납·정리", "amt": "5.7만 원", "pct": 16},
        {"cat": "조명·생활", "amt": "4.2만 원", "pct": 12},
    ],
}

FAQS = [
    {
        "q": "추천 제품은 어떻게 고르나요?",
        "a": "실제 1인 가구 사용 후기, 내구성, 가격 대비 만족도를 기준으로 추립니다. 광고비를 더 낸 제품을 위로 올리지 않습니다.",
    },
    {
        "q": "꼭 다 사야 하나요?",
        "a": '아니요. "필수 → 추천 → 선택" 순서로 표시했습니다. 예산이 빠듯하면 필수 항목만 먼저 갖추고 나머지는 천천히 채워도 됩니다.',
    },
    {
        "q": "예산 분배표는 어떻게 보나요?",
        "a": "아래 표는 추천 구성을 모두 샀을 때의 카테고리별 비중입니다. 본인 상황에 맞게 항목을 빼고 더하며 참고용으로 쓰세요.",
    },
    {
        "q": "구매 링크로 사면 가격이 오르나요?",
        "a": "아니요. 동일한 가격이며, 일부 구매에 대해 제휴 수수료를 받을 수 있습니다. 이는 사이트 운영에만 쓰입니다.",
    },
]

# 사업자 정보 — M2 결정(세션 #7): 필명 "혼살다", 이메일 확정, 등록 진행 중 표기
BUSINESS_INFO = {
    "name": "혼살림",
    "rep": "혼살다 (운영자)",
    "bizno": "등록 진행 중",
    "mailorder": "등록 진행 중",
    "email": "dugihappyending@gmail.com",
    "addr": "등록 진행 중",
}


def _related(scn):
    """같은 페르소나 또는 같은 시즌의 다른 시나리오 최대 3개 (디자인 로직 일치)."""
    return [
        x
        for x in SCENARIOS
        if x["id"] != scn["id"] and (x["persona"] == scn["persona"] or x["season"] == scn["season"])
    ][:3]


def _write(rel_path: str, html: str) -> None:
    page = OUT / rel_path
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(html, encoding="utf-8")


def build() -> Path:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    common = {
        "asset_base": "/static",
        "personas": PERSONAS,
        "business_info": BUSINESS_INFO,
    }

    OUT.mkdir(parents=True, exist_ok=True)

    # 홈
    _write(
        "index.html",
        env.get_template("home.html").render(
            active_nav="home",
            canonical_url="https://honsallim.com/",
            featured_scenarios=[s for s in SCENARIOS if s["hot"]][:6],
            season_calendar=SEASONS,
            **common,
        ),
    )

    # 시나리오 허브
    _write(
        "scenarios/index.html",
        env.get_template("scenario_list.html").render(
            active_nav="hub",
            canonical_url="https://honsallim.com/scenarios/",
            scenarios=SCENARIOS,
            budget_filters=BUDGET_FILTERS,
            season_filters=SEASON_FILTERS,
            **common,
        ),
    )

    # 페르소나 허브 (전체 + 개별)
    persona_tmpl = env.get_template("persona_hub.html")
    for i, p in enumerate(PERSONAS):
        html = persona_tmpl.render(
            active_nav="persona",
            canonical_url=f"https://honsallim.com/personas/{p['id']}/",
            persona=p,
            scenarios=[s for s in SCENARIOS if s["persona"] == p["id"]],
            **common,
        )
        _write(f"personas/{p['id']}/index.html", html)
        if i == 0:  # /personas/ 기본 = 첫 페르소나
            _write("personas/index.html", html)

    # About
    _write(
        "about/index.html",
        env.get_template("about.html").render(
            active_nav="about",
            canonical_url="https://honsallim.com/about/",
            **common,
        ),
    )

    # 상세페이지 (시나리오별)
    art_tmpl = env.get_template("article.html")
    for scn in SCENARIOS:
        _write(
            f"articles/{scn['id']}/index.html",
            art_tmpl.render(
                active_nav="hub",
                canonical_url=f"https://honsallim.com/articles/{scn['id']}/",
                article=scn,
                products=PRODUCTS,
                budget=BUDGET_TABLE,
                faqs=FAQS,
                related=_related(scn),
                **common,
            ),
        )

    # static 복사 (덮어쓰기)
    shutil.copytree(STATIC, OUT / "static", dirs_exist_ok=True)
    return OUT


if __name__ == "__main__":
    out = build()
    pages = sorted(p.relative_to(out).as_posix() for p in out.rglob("index.html"))
    print(f"[OK] 미리보기 생성: {out}  (페이지 {len(pages)}개)")
    print("     실행: python -m http.server 8787 --directory build/preview")
    print("     접속: http://localhost:8787/")
