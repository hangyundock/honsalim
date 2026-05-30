# mypy: ignore-errors
# ruff: noqa
"""혼살림 카테고리 페이지 시안 (세션 #14 프로토타입·목업) — 노써치식 흰 바탕 (사무용 의자).

본구현 전 디자인/콘텐츠 규격 프로토타입. 실행 시 흰 바탕 카테고리 페이지 HTML 생성.
표준 명세는 docs/CATEGORY_PAGE.md. 제품 데이터는 하드코딩(라이브 수집값 — 세션 #14).
"""

IMG = "https://ae-pic-a1.aliexpress-media.com/kf/"

PRODUCTS = [
    {
        "rank": "베스트픽",
        "type": "안장형 스툴",
        "name": "편안한 장시간 앉기 좋은 안장형 스툴",
        "price": "143,100원",
        "orig": "255,537원",
        "disc": "44%",
        "img": "Sc5f44a55d12d4ec6a4a6513ab06a35fbo.jpg",
        "slug": "ali-1005012210783147",
        "pros": [
            "골반을 자연스럽게 받쳐 압박 분산",
            "360° 회전·높이 조절로 잦은 움직임에 유리",
            "메모리폼 쿠션",
        ],
        "cons": ["등받이가 없어 장시간 기댐은 불가", "허리 지지보다 골반 중심"],
        "for": "자주 일어나고 회전·움직임이 많은 분",
        "spec": {
            "등받이": "없음(스툴)",
            "요추지지": "△ 골반형",
            "목받침": "X",
            "팔걸이": "X",
            "회전": "O 360°",
            "높이조절": "O",
            "소재": "메모리폼",
        },
    },
    {
        "rank": "자세교정",
        "type": "무릎꿇이 의자",
        "name": "인체공학 원목 무릎꿇이 의자",
        "price": "123,988원",
        "orig": "",
        "disc": "0%",
        "img": "S9e4e95d584fd4aa497198de39f5be57dK.jpg",
        "slug": "ali-1005012229536058",
        "pros": [
            "무릎 받침으로 척추 정렬 자연 유도",
            "흔들 기능으로 미세 움직임",
            "원목 프레임 내구성",
        ],
        "cons": ["적응 기간 필요", "장시간 같은 자세는 무릎 부담"],
        "for": "자세 교정·허리 통증을 우선하는 분",
        "spec": {
            "등받이": "보조",
            "요추지지": "O 정렬유도",
            "목받침": "X",
            "팔걸이": "X",
            "회전": "X",
            "높이조절": "O",
            "소재": "원목+쿠션",
        },
    },
    {
        "rank": "프리미엄",
        "type": "게이밍 의자",
        "name": "인체공학 게이밍 의자(리클라이닝)",
        "price": "239,264원",
        "orig": "498,467원",
        "disc": "52%",
        "img": "Scfe966753f2647b8ab7341408ea276b64.jpg",
        "slug": "ali-1005012158192141",
        "pros": ["높은 등받이·목 쿠션으로 상반신 전체 지지", "4D 팔걸이", "리클라이닝으로 휴식"],
        "cons": ["디자인이 게이밍풍(홈오피스 미관)", "부피가 큼"],
        "for": "등받이·목까지 충실한 본격 지지를 원하는 분",
        "spec": {
            "등받이": "O 하이백",
            "요추지지": "O 쿠션",
            "목받침": "O",
            "팔걸이": "O 4D",
            "회전": "O",
            "높이조절": "O",
            "소재": "레자/메시",
        },
    },
]

BUDGET = [
    {
        "rank": "가성비 풀옵션",
        "type": "요추+헤드레스트",
        "name": "인체공학 사무용 의자 (요추 지지+헤드레스트)",
        "price": "47,861원",
        "orig": "73,632원",
        "disc": "35%",
        "img": "Sbffc95aba257457ca9f98dbe9f3bef41X.jpg",
        "slug": "ali-1005010745096562",
        "pros": [
            "요추 지지대 + 헤드레스트로 목·허리 모두 받침",
            "높이 조절·회전",
            "5만원 이하 가성비",
        ],
        "cons": ["마감·내구성은 가격대 수준", "팔걸이 조절 단순"],
        "for": "5만원 이하로 목·허리 둘 다 받치고 싶은 분",
        "spec": {
            "등받이": "O 미드백",
            "요추지지": "O",
            "목받침": "O",
            "팔걸이": "△ 고정",
            "회전": "O",
            "높이조절": "O",
            "소재": "메쉬",
        },
    },
    {
        "rank": "입문 메쉬",
        "type": "기본 메쉬",
        "name": "홈오피스 메쉬 컴퓨터 의자",
        "price": "42,610원",
        "orig": "60,872원",
        "disc": "30%",
        "img": "Sf92e603eb54b4a2f92b2ba628f9814ffk.jpeg",
        "slug": "ali-1005012323147196",
        "pros": ["통기성 메쉬로 여름에도 시원", "높이 조절·360° 회전", "요추 지지"],
        "cons": ["헤드레스트 없음", "장시간 기댐엔 한계"],
        "for": "가볍게 시작하는 입문용·통기성 우선",
        "spec": {
            "등받이": "O 미드백",
            "요추지지": "O",
            "목받침": "X",
            "팔걸이": "△ 고정",
            "회전": "O 360°",
            "높이조절": "O",
            "소재": "메쉬",
        },
    },
    {
        "rank": "발받침형",
        "type": "리클라이닝+발받침",
        "name": "인체공학 게이밍 사무 의자 (발받침 포함)",
        "price": "52,633원",
        "orig": "75,191원",
        "disc": "30%",
        "img": "S858c89b25cc74646a765e74ae2586863N.jpg",
        "slug": "ali-1005012218245199",
        "pros": ["발받침대 포함 · 리클라이닝", "요추 지지 · 높이 조절", "휴식 자세 가능"],
        "cons": ["게이밍풍 디자인", "부피가 큼"],
        "for": "쉬는 자세·다리 받침까지 원하는 분",
        "spec": {
            "등받이": "O 하이백",
            "요추지지": "O",
            "목받침": "O",
            "팔걸이": "O",
            "회전": "O",
            "높이조절": "O",
            "소재": "메쉬",
        },
    },
]

SPEC_ROWS = ["등받이", "요추지지", "목받침", "팔걸이", "회전", "높이조절", "소재"]


def pros_cons(p):
    pr = "".join(f'<li class="pro">{x}</li>' for x in p["pros"])
    cn = "".join(f'<li class="con">{x}</li>' for x in p["cons"])
    return f'<ul class="pc">{pr}{cn}</ul>'


def pcard(i, p):
    return (
        f'<div class="pcard"><div class="prank">{i}. <b>{p["rank"]}</b> · {p["type"]}</div>'
        f'<div class="pmain"><div class="pleft"><a class="ph" href="/go/{p["slug"]}"><img loading="lazy" src="{IMG}{p["img"]}" alt="{p["name"]}"></a>'
        f'<div class="psig"><span>⭐ 긍정평가 <b>{p["rate"]}</b></span><span>📦 판매수량 <b>{p["sold"]}</b></span></div></div>'
        f'<div class="pinfo"><div class="pnm">{p["name"]}</div><div class="pprice">{p["price"]}</div>'
        f'{pros_cons(p)}<div class="pfor"><b>추천 대상</b> · {p["for"]}</div>'
        f'<div class="pbtns"><a class="btn primary" href="/go/{p["slug"]}">최저가/구매 보기 →</a>'
        f'<a class="btn ghost" href="#compare">VS 비교</a></div></div></div></div>'
    )


# pcard(풀폭 카드)는 2단 레이아웃 전환으로 미사용 — tcard 사용


def tcard(i, p):
    pr = "".join(f'<li class="pro">{x}</li>' for x in p["pros"])
    cn = "".join(f'<li class="con">{x}</li>' for x in p["cons"])
    disc = p.get("disc", "0%")
    sig = (
        f'<span class="tsig">정가 <s>{p.get("orig", "")}</s> · <b class="off">{disc}↓</b></span>'
        if disc not in ("0%", "")
        else ""
    )
    return (
        f'<div class="tcard"><div class="trank">{i}. <b>{p["rank"]}</b> · {p["type"]}</div>'
        f'<div class="tbody"><a class="timg" href="/go/{p["slug"]}"><img loading="lazy" src="{IMG}{p["img"]}" alt="{p["name"]}"></a>'
        f'<div class="tinfo"><div class="tnm">{p["name"]}</div><div class="tprice">{p["price"]}</div>{sig}</div></div>'
        f'<ul class="tpc">{pr}{cn}</ul>'
        f'<div class="tfor"><b>추천</b> · {p["for"]}</div>'
        f'<div class="tbtns"><a class="btn primary" href="/go/{p["slug"]}">최저가/구매 →</a><a class="btn ghost" href="#detail">더 알아보기</a></div></div>'
    )


budget_col = "".join(tcard(i + 1, p) for i, p in enumerate(BUDGET))
general_col = "".join(tcard(i + 1, p) for i, p in enumerate(PRODUCTS))

SEL = [("💰", p) for p in BUDGET] + [("⭐", p) for p in PRODUCTS]
typesel_html = "".join(
    f'<div class="tsel{" on" if i == 0 else ""}"><div class="ti"><img loading="lazy" src="{IMG}{p["img"]}"></div>'
    f'<div class="tl">{em} {p["type"]}</div></div>'
    for i, (em, p) in enumerate(SEL)
)

# 비교표
CMP = [("실속", p) for p in BUDGET] + [("고급", p) for p in PRODUCTS]
head = "".join(
    f'<th><div class="cth"><span class="ctier t-{tier}">{tier}</span><img loading="lazy" src="{IMG}{p["img"]}"><span>{p["type"]}<br><b>{p["price"]}</b></span></div></th>'
    for tier, p in CMP
)
rows = ""
for r in SPEC_ROWS:
    cells = "".join(f"<td>{p['spec'].get(r, '—')}</td>" for tier, p in CMP)
    rows += f"<tr><th>{r}</th>{cells}</tr>"
compare_table = f'<div class="cmp-wrap"><table class="cmp"><thead><tr><th>항목</th>{head}</tr></thead><tbody>{rows}</tbody></table></div>'

HTML = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>사무용 의자 고르는 법 + 추천 3 | 혼살림</title>
<link href="https://fonts.cdnfonts.com/css/nanumsquare-neo" rel="stylesheet">
<style>
:root{{--ink:#23272c;--sub:#3f464e;--meta:#5a626b;--line:#e6e8eb;--bg:#fff;--soft:#f6f7f9;--accent:#1f7a5e;--accentink:#155c46;--pro:#1f7a5e;--con:#b04a3a}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:"NanumSquare Neo","NanumSquareNeo","Pretendard","Apple SD Gothic Neo",system-ui,sans-serif;background:var(--bg);color:var(--ink);line-height:1.65;-webkit-font-smoothing:antialiased}}
a{{text-decoration:none;color:inherit}} img{{display:block;max-width:100%}}
.wrap{{max-width:900px;margin:0 auto;padding:0 20px}}
.mockbar{{background:#222;color:#eee;text-align:center;font-size:12.5px;padding:7px}}.mockbar b{{color:#fff}}
/* header */
.hdr{{border-bottom:1px solid var(--line);position:sticky;top:0;background:rgba(255,255,255,.96);backdrop-filter:blur(8px);z-index:50}}
.hdr-in{{display:flex;align-items:center;gap:26px;height:58px;max-width:1100px;margin:0 auto;padding:0 20px}}
.logo{{font-size:20px;font-weight:800;color:var(--accent)}}
.nav{{display:flex;gap:18px;margin-left:8px}}
.nav a{{font-size:14.5px;color:var(--sub);font-weight:500}} .nav a.on{{color:var(--ink);font-weight:700}}
.util{{margin-left:auto;font-size:13.5px;color:var(--meta)}}
/* category bar */
.catbar{{border-bottom:1px solid var(--line);background:var(--soft)}}
.catbar-in{{max-width:900px;margin:0 auto;padding:14px 20px 0;}}
.catname{{font-size:18px;font-weight:800}}
.tabs{{display:flex;gap:22px;margin-top:12px}}
.tabs a{{font-size:14px;color:var(--meta);font-weight:600;padding-bottom:11px;border-bottom:2px solid transparent}}
.tabs a.on{{color:var(--accent);border-color:var(--accent)}}
.main{{padding:26px 0 70px}}
.crumb{{font-size:12.5px;color:var(--meta);margin-bottom:14px}}
.disc{{display:flex;gap:9px;background:var(--soft);border:1px solid var(--line);border-radius:8px;padding:11px 14px;font-size:12.5px;color:var(--sub);margin-bottom:18px}}
.disc b{{color:var(--ink)}}
/* 타입 셀렉터 */
.typesel{{display:flex;gap:10px;overflow:auto;padding-bottom:4px;margin-bottom:20px}}
.tsel{{flex:0 0 auto;width:120px;border:1px solid var(--line);border-radius:10px;overflow:hidden;background:#fff}}
.tsel.on{{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent)}}
.tsel .ti{{height:84px;background:#f2f3f5;display:flex;align-items:center;justify-content:center;overflow:hidden}}
.tsel .ti img{{width:100%;height:100%;object-fit:contain}}
.tsel .tl{{font-size:12.5px;font-weight:700;text-align:center;padding:7px 4px;color:var(--ink)}}
h1{{font-size:28px;font-weight:800;letter-spacing:-.02em;line-height:1.3;margin:6px 0 12px}}
.byline{{display:flex;align-items:center;gap:9px;font-size:13px;color:var(--meta);margin-bottom:6px}}
.byline .av{{width:24px;height:24px;border-radius:50%;background:var(--accent);color:#fff;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700}}
.byline .au{{color:var(--ink);font-weight:700}}
.lead{{font-size:15.5px;color:var(--sub);margin:14px 0;line-height:1.8}}
.lead b{{color:var(--ink)}}
/* 신뢰 박스 */
.box{{background:var(--soft);border:1px solid var(--line);border-radius:10px;padding:15px 17px;margin:16px 0}}
.box .bt{{font-size:14px;font-weight:800;margin-bottom:6px}}
.box p{{font-size:13px;color:var(--sub);line-height:1.7}}
.tier-intro{{font-size:14px;color:var(--sub);margin:2px 0 14px;line-height:1.7}}.tier-intro b{{color:var(--ink)}}
.tier-label{{font-size:14.5px;font-weight:800;color:var(--ink);margin:22px 0 10px;padding:7px 13px;background:var(--soft);border-left:3px solid var(--accent);border-radius:6px}}
.tier-note{{font-size:13.5px;color:var(--sub);border:1px dashed #cfd4da;border-radius:10px;padding:14px 16px;margin-bottom:8px;line-height:1.6}}.tier-note b{{color:var(--ink)}}
/* 섹션 라벨(검정) */
.sechead{{margin:42px 0 16px;padding-left:14px;border-left:4px solid var(--accent)}}
.sechead .eb{{font-size:12px;font-weight:800;letter-spacing:.12em;color:var(--accent)}}
.sechead h2{{font-size:21px;font-weight:800;color:var(--ink);line-height:1.3;margin-top:3px}}
.sub-h{{font-size:16px;font-weight:800;margin:26px 0 8px;color:var(--ink)}}
.p{{font-size:14.5px;color:var(--sub);margin:9px 0;line-height:1.8}}
.p b{{color:var(--ink)}}
ul.chk{{list-style:none;margin:10px 0}}
ul.chk li{{font-size:14px;color:var(--sub);padding:7px 0 7px 24px;position:relative;border-bottom:1px dashed var(--line);line-height:1.6}}
ul.chk li:before{{content:"✓";position:absolute;left:0;color:var(--accent);font-weight:800}}
ul.chk li b{{color:var(--ink)}}
/* 개념 이미지 placeholder */
.concept{{background:repeating-linear-gradient(45deg,#f4f5f7,#f4f5f7 10px,#eef0f2 10px,#eef0f2 20px);border:1px dashed #cfd4da;border-radius:10px;padding:30px;text-align:center;color:#9aa3ad;font-size:13px;margin:14px 0}}
.concept b{{color:#7c8590}}
/* 타입 비교 표 / 스펙 비교 표 */
table{{width:100%;border-collapse:collapse;font-size:13.5px;margin:14px 0;background:#fff;border:1px solid var(--line);border-radius:10px;overflow:hidden}}
th,td{{padding:10px 12px;text-align:left;border-bottom:1px solid var(--line)}}
thead th{{background:var(--soft);font-weight:700;color:var(--ink);font-size:13px}}
td{{color:var(--sub)}}
table.cmp th:first-child,table.cmp td:first-child{{background:var(--soft);font-weight:700;color:var(--ink);width:96px}}
.cth{{display:flex;flex-direction:column;align-items:center;gap:6px;text-align:center}}
.cth img{{width:54px;height:54px;object-fit:contain;background:#f2f3f5;border-radius:7px}}
.cth b{{color:var(--accent)}}
.cmp-wrap{{overflow-x:auto}}
table.cmp{{min-width:720px}}
.ctier{{display:inline-block;font-size:10px;font-weight:800;color:#fff;border-radius:4px;padding:1px 7px}}
.ctier.t-실속{{background:var(--accent)}}
.ctier.t-고급{{background:#7a6a4d}}
/* 추천 카드 */
.pcard{{border:1px solid var(--line);border-radius:12px;padding:16px;margin:14px 0;background:#fff}}
.prank{{font-size:13px;color:var(--meta);margin-bottom:12px}} .prank b{{color:var(--accent)}}
.pmain{{display:flex;gap:18px}}
.pleft{{flex:0 0 160px;display:flex;flex-direction:column;gap:8px}}
.ph{{width:160px;height:160px;background:#f2f3f5;border:1px solid var(--line);border-radius:10px;display:flex;align-items:center;justify-content:center;overflow:hidden}}
.psig{{display:flex;flex-direction:column;gap:3px;font-size:12px;color:var(--sub);background:var(--soft);border:1px solid var(--line);border-radius:8px;padding:8px 10px;text-align:center}}
.psig b{{color:var(--ink);font-weight:800}}
.ph img{{width:100%;height:100%;object-fit:contain}}
.pinfo{{flex:1;min-width:0}}
.pnm{{font-size:16px;font-weight:700;line-height:1.4}}
.pprice{{font-size:20px;font-weight:800;color:var(--ink);margin:6px 0 10px}}
ul.pc{{list-style:none;display:grid;gap:4px;margin-bottom:10px}}
ul.pc li{{font-size:13.5px;padding-left:20px;position:relative;color:var(--sub);line-height:1.55}}
ul.pc li.pro:before{{content:"＋";position:absolute;left:0;color:var(--pro);font-weight:800}}
ul.pc li.con:before{{content:"－";position:absolute;left:0;color:var(--con);font-weight:800}}
.pfor{{font-size:13px;color:var(--sub);background:var(--soft);border-radius:7px;padding:8px 11px;margin-bottom:12px}}
.pfor b{{color:var(--accentink)}}
.pbtns{{display:flex;gap:8px}}
.btn{{font-size:13.5px;font-weight:700;padding:10px 16px;border-radius:8px}}
.btn.primary{{background:var(--accent);color:#fff}}
.btn.ghost{{background:#fff;color:var(--accentink);border:1px solid var(--line)}}
.alt{{border:1px solid var(--line);border-radius:10px;padding:13px 15px;margin:9px 0;font-size:13.5px;color:var(--sub)}}
.alt b{{color:var(--ink)}}
.faq details{{border:1px solid var(--line);border-radius:9px;padding:12px 15px;margin-bottom:8px}}
.faq summary{{font-weight:700;cursor:pointer;list-style:none;font-size:14px}}.faq summary::-webkit-details-marker{{display:none}}
.faq p{{font-size:13.5px;color:var(--sub);margin-top:8px}}
.foot{{border-top:1px solid var(--line);margin-top:36px;padding-top:18px;font-size:12px;color:var(--meta);line-height:1.7}}
.tiers{{display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:start;margin-top:8px}}
.tier-col{{min-width:0}}
.tcard{{border:1px solid var(--line);border-radius:12px;padding:13px;margin-bottom:12px;background:#fff}}
.trank{{font-size:11.5px;color:var(--meta);font-weight:600}}.trank b{{color:var(--accent)}}
.tbody{{display:flex;gap:11px;margin:7px 0}}
.timg{{flex:0 0 84px;width:84px;height:84px;border:1px solid var(--line);border-radius:8px;background:#fff;display:flex;align-items:center;justify-content:center;overflow:hidden}}
.timg img{{width:100%;height:100%;object-fit:contain}}
.tinfo{{flex:1;min-width:0}}
.tnm{{font-size:13.5px;font-weight:700;line-height:1.35;color:var(--ink)}}
.tprice{{font-size:17px;font-weight:800;color:var(--ink);margin:3px 0 5px}}
.tsig{{font-size:11px;color:var(--sub);background:var(--soft);border:1px solid var(--line);border-radius:6px;padding:4px 8px;display:inline-block}}.tsig s{{color:var(--meta)}}.tsig .off{{color:#c0392b;font-weight:800}}
ul.tpc{{list-style:none;margin:6px 0;display:grid;gap:3px}}
ul.tpc li{{font-size:12px;padding-left:15px;position:relative;color:var(--sub);line-height:1.45}}
ul.tpc li.pro:before{{content:"＋";position:absolute;left:0;color:var(--pro);font-weight:800}}
ul.tpc li.con:before{{content:"－";position:absolute;left:0;color:var(--con);font-weight:800}}
.tfor{{font-size:12px;color:var(--sub);background:var(--soft);border-radius:6px;padding:7px 10px;margin-bottom:9px}}.tfor b{{color:var(--accentink)}}
.tbtns{{display:flex;gap:6px}}
.tbtns .btn{{font-size:12px;padding:8px 11px;flex:1;text-align:center}}
@media(max-width:760px){{.nav{{display:none}}.pmain{{flex-direction:column}}.pleft{{flex:none;width:100%}}.ph{{width:100%;height:200px}}.tiers{{grid-template-columns:1fr}}h1{{font-size:22px}}}}
</style></head><body>
<div class="mockbar">🅼 <b>카테고리 페이지 시안</b> · 노써치식 흰 바탕 · 저자=혼살다 · 제품·이미지·가격=실데이터 / 가이드 글=예시(혼살다 작성 예정)</div>
<header class="hdr"><div class="hdr-in"><span class="logo">혼살림</span>
<nav class="nav"><a>홈</a><a class="on">카테고리</a><a>구매가이드</a><a>세팅</a><a>About</a></nav>
<span class="util">🔍 &nbsp; 로그인</span></div></header>
<div class="catbar"><div class="catbar-in"><div class="catname">사무용 의자 ▾</div>
<div class="tabs"><a>통합</a><a class="on">추천·비교</a><a>구매가이드</a><a>전체 제품</a></div></div></div>
<main class="wrap main">
<div class="crumb">홈 › 카테고리 › 사무용 의자</div>
<div class="disc"><span>ⓘ</span><span><b>대가성 안내</b> · 이 글에는 AliExpress 어필리에이트 활동의 일환으로 일정 수수료를 제공받습니다. (구매자에게 추가 비용은 발생하지 않습니다.)</span></div>

<div class="typesel">{typesel_html}</div>

<h1>재택 8시간 버티는 사무용 의자 고르는 법 + 추천 3</h1>
<div class="byline"><span class="av">혼</span><span class="au">혼살다</span> · 2026.05.30 업데이트 · 🔖 공유 · 💬 0</div>

<p class="lead">사무용 의자는 디자인이 아니라 <b>'얼마나 오래, 어떻게 앉느냐'</b>로 골라야 합니다. 하루 8시간 앉는 재택근무라면 의자 한 번 잘못 고르면 허리·목·어깨가 1년 내내 고생합니다. 이 글은 <b>의자를 고를 때 꼭 봐야 할 기준</b>과, 1인 가구·재택 관점에서 추천 3가지를 비교합니다.</p>

<div class="box"><div class="bt">🤝 혼살림의 약속</div><p>혼살림은 <b>제조사로부터 광고비·협찬을 받지 않습니다.</b> 위 고지처럼 제휴 링크로 구매가 일어나면 판매처에서 수수료를 받지만, 그 수수료는 <b>어떤 제품을 추천할지와는 무관</b>합니다. 추천 기준은 오직 1인 가구 독자에게 도움이 될 수 있도록 객관적으로 평가했습니다.</p></div>
<div class="box"><div class="bt">📋 이렇게 골랐어요</div><p>판매자가 표기한 스펙·옵션과 가격·할인을 <b>1인 가구·재택 환경 기준</b>(오래 앉아도 편한가 · 공간에 맞는가 · 오래 쓰는가)으로 따져 비교·정리했습니다. <span class="dim">가격·할인은 수집 시점 기준이며 변동될 수 있습니다.</span></p></div>

<div class="sechead"><div class="eb">고르는 법</div><h2>사무용 의자, 사기 전 꼭 확인할 것</h2></div>

<div class="sub-h">1. 의자는 '착좌 시간'으로 타입이 갈립니다</div>
<p class="p">오래 앉아 집중하는지, 자주 일어나고 움직이는지에 따라 맞는 타입이 다릅니다. 한 의자가 모두에게 정답이 아닙니다.</p>
<div class="concept">🖼 <b>개념 이미지(디자인 AI 생성 예정)</b> — 안장형 vs 무릎꿇이 vs 하이백 자세·지지 비교 일러스트</div>
<table><thead><tr><th>타입</th><th>지지 방식</th><th>이런 분께</th></tr></thead><tbody>
<tr><td><b>안장형 스툴</b></td><td>골반 받침·등받이 없음</td><td>자주 일어나고 회전·움직임 많음</td></tr>
<tr><td><b>무릎꿇이</b></td><td>척추 정렬 유도</td><td>자세 교정·허리 통증</td></tr>
<tr><td><b>하이백/게이밍</b></td><td>등받이·목 전체 지지</td><td>오래 기대고 앉는 집중 업무</td></tr>
</tbody></table>

<div class="sub-h">2. 고르기 전 꼭 체크할 6가지 (왜 중요한지)</div>
<ul class="chk">
<li><b>요추(허리) 지지</b> — 8시간 착좌 시 허리 디스크 압력이 서 있을 때의 1.4배. 요추 곡선을 받쳐주는지가 1순위.</li>
<li><b>등받이 높이·목받침</b> — 모니터를 올려다보면 목·어깨가 결림. 기대는 업무엔 목받침 유무가 큼.</li>
<li><b>팔걸이 조절(2D/3D/4D)</b> — 팔 높이가 안 맞으면 어깨가 들려 통증. 높이만이라도 조절되는지 확인.</li>
<li><b>좌판 높이·깊이·회전</b> — 발이 바닥에 닿고 무릎 90°가 기본. 체형에 맞는 조절 폭이 중요.</li>
<li><b>소재·통기성</b> — 메시는 통기성, 폼은 쿠션감. 장시간엔 통기성도 피로에 영향.</li>
<li><b>가스실린더·하중·내구성</b> — 저가 의자의 흔한 실수: 가스실린더 등급(SHKS 인증)·내하중 미확인 → 주저앉음. 후기에서 '몇 개월 만에 내려앉음' 체크.</li>
</ul>

<div class="sub-h">3. 흔한 실수</div>
<p class="p">① <b>디자인만 보고 고르기</b> — 예뻐도 요추 지지가 없으면 8시간엔 독. ② <b>팔걸이 고정형</b> — 책상 높이와 안 맞아 어깨 부담. ③ <b>가성비만</b> — 가스실린더·프레임 부실은 후기로 거른다.</p>

<div class="sechead"><div class="eb">추천 · 비교</div><h2>혼살림이 고른 사무용 의자</h2></div>
<p class="tier-intro">예산에 따라 <b>두 가지</b>로 비교합니다 — <b>💰 실속형</b>(가볍게 시작) / <b>⭐ 고급형</b>(오래 쓸 본격). <span class="dim">그 이상 프리미엄급은 1인 자취엔 과해서 다루지 않습니다.</span></p>
<div class="tiers">
<div class="tier-col"><div class="tier-label">💰 실속형 · 4~5만원대 · 알리 라이브</div>{budget_col}</div>
<div class="tier-col"><div class="tier-label">⭐ 고급형 · 12~24만원대</div>{general_col}</div>
</div>
<div id="compare"></div>

<div class="sub-h">한눈에 비교</div>
{compare_table}

<div class="sub-h">같이 고려해 볼 만한 옵션</div>
<div class="alt"><b>메시 사무용 의자(통기성 우선)</b> — 여름철 땀·통기성이 걱정이면 풀메시 등받이형. <span style="color:#8a93a0">· 수집 후 비교 추가 예정</span></div>
<div class="alt"><b>헤드레스트 분리형 고급형</b> — 목받침·요추 별도 조절이 필요하면 상위 옵션. <span style="color:#8a93a0">· 수집 후 비교 추가 예정</span></div>

<div class="sub-h faq" style="margin-top:30px">자주 묻는 질문</div>
<div class="faq">
<details open><summary>의자와 책상 중 어디에 더 투자해야 하나요?</summary><p>의자입니다. 척추·골반에 직접 영향을 주므로 의자에 예산을 먼저 배분하세요.</p></details>
<details><summary>게이밍 의자, 재택에 써도 되나요?</summary><p>등받이·목·팔걸이 지지가 좋아 기능상 적합합니다. 디자인이 게이밍풍인 점만 고려하세요.</p></details>
<details><summary>메시와 폼(쿠션), 뭐가 나아요?</summary><p>통기성·여름엔 메시, 쿠션감·푹신함은 폼. 장시간 착좌면 통기성도 피로에 영향을 줍니다.</p></details>
</div>

<div class="foot">혼살림은 위 추천 항목 중 일부에 제휴(어필리에이트) 링크를 사용하며, 구매 시 일정액의 수수료를 받을 수 있습니다. 이는 구매 가격에 영향을 주지 않으며, 추천 선정과 무관합니다. · 상호 혼살림 · 문의 dugihappyending@gmail.com</div>
</main></body></html>"""

open("docs/design_drafts/honsalim/category_mock.html", "w", encoding="utf-8").write(HTML)
open("docs/design_drafts/honsalim/redesign/index.html", "w", encoding="utf-8").write(HTML)
print("OK category page mock. products:", len(PRODUCTS), "len:", len(HTML))
