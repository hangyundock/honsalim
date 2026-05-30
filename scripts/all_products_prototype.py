# mypy: ignore-errors
# ruff: noqa
"""혼살림 '전체 제품' 카탈로그 페이지 시안 (세션 #16) — 데이터 주도형.

"더 많은 제품 보기"(전체 제품 탭) 레이아웃. 노써치 '랭킹'과 달리 평점·점수 데이터가 없으므로
(§0 진실성) **가격·할인·타입 필터/정렬 카탈로그**. 표준: docs/CATEGORY_PAGE.md §5-bis.

- render_catalog(category_name, items) : 상품 리스트 → 카탈로그 HTML (실수집/샘플 공용).
  items 원소: {tier:"실속"|"고급", type, name, price(str), orig(str|""), disc(str|""), img_url, slug}
- __main__ : 사무용 의자 샘플 6개로 목업 생성(레이아웃 확인용).
"""

CSS = """
:root{--ink:#23272c;--sub:#3f464e;--meta:#5a626b;--line:#e6e8eb;--bg:#fff;--soft:#f6f7f9;--accent:#1f7a5e;--accentink:#155c46;--off:#c0392b}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"NanumSquare Neo","NanumSquareNeo","Pretendard","Apple SD Gothic Neo",system-ui,sans-serif;background:var(--bg);color:var(--ink);line-height:1.6}
a{text-decoration:none;color:inherit} img{display:block;max-width:100%}
.mockbar{background:#222;color:#eee;text-align:center;font-size:12.5px;padding:7px}.mockbar b{color:#fff}
.hdr{border-bottom:1px solid var(--line);position:sticky;top:0;background:rgba(255,255,255,.96);backdrop-filter:blur(8px);z-index:50}
.hdr-in{display:flex;align-items:center;gap:26px;height:58px;max-width:1100px;margin:0 auto;padding:0 20px}
.logo{font-size:20px;font-weight:800;color:var(--accent)}
.nav{display:flex;gap:18px;margin-left:8px} .nav a{font-size:14.5px;color:var(--sub);font-weight:500}
.catbar{border-bottom:1px solid var(--line);background:var(--soft)}
.catbar-in{max-width:1000px;margin:0 auto;padding:14px 20px 0}
.catname{font-size:18px;font-weight:800}
.tabs{display:flex;gap:22px;margin-top:12px}
.tabs a{font-size:14px;color:var(--meta);font-weight:600;padding-bottom:11px;border-bottom:2px solid transparent}
.tabs a.on{color:var(--accent);border-color:var(--accent)}
.wrap{max-width:1000px;margin:0 auto;padding:0 20px}
.main{padding:24px 0 70px}
.crumb{font-size:12.5px;color:var(--meta);margin-bottom:12px}
.disc{display:flex;gap:9px;background:var(--soft);border:1px solid var(--line);border-radius:8px;padding:11px 14px;font-size:12.5px;color:var(--sub);margin-bottom:16px}
.disc b{color:var(--ink)}
h1{font-size:24px;font-weight:800;letter-spacing:-.02em;margin:4px 0 8px}
.lead{font-size:14px;color:var(--sub);margin-bottom:18px;line-height:1.7}.lead b{color:var(--ink)}
.sortbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:14px}
.sortbar .lbl{font-size:13px;color:var(--meta);font-weight:700;margin-right:2px}
.sort{font-size:13.5px;font-weight:700;padding:7px 14px;border-radius:20px;border:1px solid var(--line);background:#fff;color:var(--sub);cursor:pointer}
.sort.on{background:var(--accent);color:#fff;border-color:var(--accent)}
.filters{display:flex;flex-direction:column;gap:9px;background:var(--soft);border:1px solid var(--line);border-radius:10px;padding:13px 15px;margin-bottom:16px}
.frow{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.frow .fl{font-size:12.5px;color:var(--meta);font-weight:800;width:54px;flex:0 0 54px}
.chip{font-size:12.5px;font-weight:600;padding:5px 12px;border-radius:16px;border:1px solid var(--line);background:#fff;color:var(--sub);cursor:pointer}
.chip.on{background:#eaf5f0;border-color:var(--accent);color:var(--accentink);font-weight:800}
.countbar{display:flex;justify-content:space-between;align-items:center;font-size:13px;color:var(--meta);margin-bottom:12px}
.countbar b{color:var(--ink)}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.card{border:1px solid var(--line);border-radius:12px;padding:13px;background:#fff;display:flex;flex-direction:column}
.badges{display:flex;gap:6px;margin-bottom:9px}
.tier{font-size:11px;font-weight:800;color:#fff;border-radius:5px;padding:2px 8px}
.tier.t-실속{background:var(--accent)} .tier.t-고급{background:#7a6a4d}
.typ{font-size:11.5px;font-weight:700;color:var(--meta);background:var(--soft);border-radius:5px;padding:2px 8px}
.card .img{height:160px;background:#f2f3f5;border:1px solid var(--line);border-radius:9px;display:flex;align-items:center;justify-content:center;overflow:hidden;margin-bottom:10px}
.card .img img{width:100%;height:100%;object-fit:contain}
.nm{font-size:14px;font-weight:700;line-height:1.4;min-height:40px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.price{font-size:19px;font-weight:800;color:var(--ink);margin:7px 0 3px}
.sig{font-size:11.5px;color:var(--sub);display:inline-block;margin-bottom:11px}.sig s{color:var(--meta)}.sig .off{color:var(--off);font-weight:800}.sig.nodisc{color:var(--meta)}
.btns{display:flex;gap:6px;margin-top:auto}
.btn{font-size:12.5px;font-weight:700;padding:9px 12px;border-radius:8px;text-align:center}
.btn.primary{background:var(--accent);color:#fff;flex:1}
.btn.ghost{background:#fff;color:var(--accentink);border:1px solid var(--line)}
.more{text-align:center;margin:22px 0}
.more .btn{display:inline-block;padding:11px 26px;border:1px solid var(--line);color:var(--accentink);font-weight:800}
.honest{margin-top:18px;font-size:12px;color:var(--meta);background:var(--soft);border:1px dashed #cfd4da;border-radius:9px;padding:12px 15px;line-height:1.7}
.honest b{color:var(--ink)}
.foot{border-top:1px solid var(--line);margin-top:30px;padding-top:16px;font-size:12px;color:var(--meta);line-height:1.7}
@media(max-width:760px){.nav{display:none}.grid{grid-template-columns:repeat(2,1fr);gap:10px}.card .img{height:120px}h1{font-size:21px}.nm{min-height:36px;font-size:13px}}
"""


def card(it):
    disc = (it.get("disc") or "").strip()
    orig = (it.get("orig") or "").strip()
    sig = (
        f'<span class="sig">정가 <s>{orig}</s> · <b class="off">{disc}↓</b></span>'
        if disc and disc not in ("0%", "0") and orig
        else '<span class="sig nodisc">단일가</span>'
    )
    tier = it.get("tier", "실속")
    tier_cls = "t-실속" if tier == "실속" else "t-고급"
    tier_em = "💰 실속" if tier == "실속" else "⭐ 고급"
    return (
        f'<div class="card">'
        f'<div class="badges"><span class="tier {tier_cls}">{tier_em}</span>'
        f'<span class="typ">{it.get("type","")}</span></div>'
        f'<a class="img" href="/go/{it["slug"]}"><img loading="lazy" src="{it["img_url"]}" alt="{it["name"]}"></a>'
        f'<div class="nm">{it["name"]}</div>'
        f'<div class="price">{it["price"]}</div>{sig}'
        f'<div class="btns"><a class="btn primary" href="/go/{it["slug"]}">최저가/구매 →</a>'
        f'<a class="btn ghost" href="#vs">VS</a></div>'
        f"</div>"
    )


def render_catalog(category_name, items, total_note=None):
    cards_html = "".join(card(it) for it in items)
    note = total_note or f"{len(items)}개"
    types = []
    for it in items:
        t = (it.get("type") or "").strip()
        if t and t not in types:
            types.append(t)
    type_chips = "".join(f'<span class="chip">{t}</span>' for t in types[:8])
    return f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{category_name} 전체 제품 | 혼살림</title>
<link href="https://fonts.cdnfonts.com/css/nanumsquare-neo" rel="stylesheet">
<style>{CSS}</style></head><body>
<div class="mockbar">🅼 <b>전체 제품 카탈로그</b> · <b>점수 없음</b>(노써치 랭킹과 다름) · 가격·할인·타입 필터/정렬 · {note}</div>
<header class="hdr"><div class="hdr-in"><span class="logo">혼살림</span>
<nav class="nav"><a>홈</a><a>카테고리</a><a>구매가이드</a><a>스토어</a><a>About</a></nav></div></header>
<div class="catbar"><div class="catbar-in"><div class="catname">{category_name} ▾</div>
<div class="tabs"><a>통합</a><a>추천·비교</a><a>구매가이드</a><a class="on">전체 제품</a></div></div></div>
<main class="wrap main">
<div class="crumb">홈 › 카테고리 › {category_name} › 전체 제품</div>
<div class="disc"><span>ⓘ</span><span><b>대가성 안내</b> · 이 페이지에는 AliExpress 어필리에이트 링크가 포함되며 일정 수수료를 제공받습니다. (구매자 추가 비용 없음)</span></div>
<h1>{category_name} — 전체 제품</h1>
<p class="lead">혼살림이 <b>엄선한 추천</b>은 <b>[추천·비교]</b> 탭에 있습니다. 여기서는 같은 카테고리 전체를 <b>가격·할인·타입으로 직접</b> 골라보세요. <span style="color:#8a93a0">· 가격·할인은 수집 시점 기준이며 변동될 수 있습니다.</span></p>
<div class="sortbar"><span class="lbl">정렬</span>
<span class="sort on">추천순</span><span class="sort">낮은 가격순</span><span class="sort">할인율 높은순</span></div>
<div class="filters">
<div class="frow"><span class="fl">티어</span><span class="chip on">전체</span><span class="chip">💰 실속형</span><span class="chip">⭐ 고급형</span></div>
<div class="frow"><span class="fl">가격대</span><span class="chip on">전체</span><span class="chip">~5만</span><span class="chip">5–10만</span><span class="chip">10–20만</span><span class="chip">20만+</span></div>
<div class="frow"><span class="fl">타입</span><span class="chip on">전체</span>{type_chips}</div>
</div>
<div class="countbar"><span>전체 <b>{len(items)}</b>개 · 추천순</span><span>가격·할인 기준 정렬</span></div>
<div class="grid">{cards_html}</div>
<div class="more"><a class="btn" href="#">더 보기 ↓</a></div>
<div class="honest"><b>혼살림은 제품에 점수·평점을 매기지 않습니다.</b> 위 순서는 <b>가격·할인율 기준 정렬</b>이며 품질 순위가 아닙니다. 노써치 같은 랩테스트 점수가 아니라, 판매처가 표기한 가격·정가·할인·타입을 1인 가구 관점에서 모아 <b>직접 비교·선택</b>하시도록 돕는 카탈로그입니다.</div>
<div class="foot">혼살림은 위 항목 중 일부에 제휴(어필리에이트) 링크를 사용하며, 구매 시 일정액의 수수료를 받을 수 있습니다. 이는 구매 가격에 영향을 주지 않으며, 추천 선정과 무관합니다. · 상호 혼살림 · 문의 dugihappyending@gmail.com</div>
</main></body></html>"""


if __name__ == "__main__":
    import os

    IMG = "https://ae-pic-a1.aliexpress-media.com/kf/"
    SAMPLE = [
        {
            "tier": "실속",
            "type": "요추+헤드레스트",
            "name": "인체공학 사무용 의자 (요추 지지+헤드레스트)",
            "price": "47,861원",
            "orig": "73,632원",
            "disc": "35%",
            "img_url": IMG + "Sbffc95aba257457ca9f98dbe9f3bef41X.jpg",
            "slug": "ali-1005010745096562",
        },
        {
            "tier": "실속",
            "type": "기본 메쉬",
            "name": "홈오피스 메쉬 컴퓨터 의자",
            "price": "42,610원",
            "orig": "60,872원",
            "disc": "30%",
            "img_url": IMG + "Sf92e603eb54b4a2f92b2ba628f9814ffk.jpeg",
            "slug": "ali-1005012323147196",
        },
        {
            "tier": "실속",
            "type": "리클라이닝+발받침",
            "name": "인체공학 게이밍 사무 의자 (발받침 포함)",
            "price": "52,633원",
            "orig": "75,191원",
            "disc": "30%",
            "img_url": IMG + "S858c89b25cc74646a765e74ae2586863N.jpg",
            "slug": "ali-1005012218245199",
        },
        {
            "tier": "고급",
            "type": "안장형 스툴",
            "name": "편안한 장시간 앉기 좋은 안장형 스툴",
            "price": "143,100원",
            "orig": "255,537원",
            "disc": "44%",
            "img_url": IMG + "Sc5f44a55d12d4ec6a4a6513ab06a35fbo.jpg",
            "slug": "ali-1005012210783147",
        },
        {
            "tier": "고급",
            "type": "무릎꿇이 의자",
            "name": "인체공학 원목 무릎꿇이 의자",
            "price": "123,988원",
            "orig": "",
            "disc": "",
            "img_url": IMG + "S9e4e95d584fd4aa497198de39f5be57dK.jpg",
            "slug": "ali-1005012229536058",
        },
        {
            "tier": "고급",
            "type": "게이밍 의자",
            "name": "인체공학 게이밍 의자(리클라이닝)",
            "price": "239,264원",
            "orig": "498,467원",
            "disc": "52%",
            "img_url": IMG + "Scfe966753f2647b8ab7341408ea276b64.jpg",
            "slug": "ali-1005012158192141",
        },
    ]
    html = render_catalog("사무용 의자", SAMPLE, total_note="샘플 6개(실제 60+개)")
    os.makedirs("docs/design_drafts/honsalim", exist_ok=True)
    open("docs/design_drafts/honsalim/all_products_mock.html", "w", encoding="utf-8").write(html)
    open("docs/design_drafts/honsalim/index.html", "w", encoding="utf-8").write(html)
    print("OK all-products catalog mock (sample). items:", len(SAMPLE), "len:", len(html))
