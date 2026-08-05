"""validator.site_audit — 배포 산출물 전수 감사 (세션 #51).

★왜 이 모듈이 필요한가
    무인 시스템에 **생산 자동화는 있는데 감시 자동화가 없었다**. 배포 후 검증이 홈 1페이지의
    HTTP 상태코드만 봐서, 글↔글 내부링크가 0개여도·전 페이지 og:image가 없어도 매일 '정상'으로
    보고됐다(40일간 아무도 몰랐다 — #51 주인 적발). 사람이 라이브 HTML을 손으로 뜯어야만
    보이는 종류의 결함이라, 사람에게 맡기면 또 놓친다.

★설계 원칙
    - **단일 진실원**: doctor(사람이 볼 때)와 배포 게이트(무인이 매일)가 이 모듈 하나를 쓴다.
      각자 따로 구현하면 "doctor는 통과인데 게이트는 막힘" 같은 어긋남이 생긴다.
    - **순수 함수**: 출력·부작용 없음. 호출부가 표시/차단을 결정한다. 테스트가 쉬워진다.
    - **fail은 검색 노출·정책 위반에 직접 영향을 주는 것만**. 과민한 게이트는 발행을 막아
      비용을 폭증시킨다(#48 교훈). 나머지는 warn으로 가시화만 한다.
"""

from __future__ import annotations

import difflib
import json
import re
from dataclasses import dataclass
from pathlib import Path

SITE_ORIGIN = "https://honsallim.com"

# 공정위 대가성 고지 판정어(POLICY §2-2). 첫머리 노출이 요건이라 본문 앞부분에서 찾는다.
_DISCLOSURE_TERMS = ("수수료", "제휴", "어필리에이트")
_DISCLOSURE_HEAD_CHARS = 1200

# 본문 유사도 경고선 — 같은 카테고리 글은 구조·카탈로그를 공유해 어느 정도 겹치는 게 정상이라
# 낮게 잡으면 전부 걸린다. #51 실측 분포: 최고 0.74(실리콘도마↔스텐도마), 0.65+ 6쌍.
# 그래서 실측 최고치보다 위인 0.80을 '양산 의심' 경고선으로 둔다(차단 아님·판단은 주인).
_SIMILARITY_WARN = 0.80
_SIMILARITY_SAMPLE = 4000  # 비교 표본 길이(전문 비교는 O(n²)로 느려짐)


@dataclass(frozen=True)
class Finding:
    """감사 결과 1건. severity: 'fail'(배포 차단) | 'warn'(가시화만)."""

    severity: str
    code: str
    message: str


def _pages(site: Path) -> dict[str, str]:
    """배포 산출물 → {URL 경로: HTML}. index.html 기준."""
    out: dict[str, str] = {}
    for p in site.rglob("index.html"):
        rel = "/" + str(p.parent.relative_to(site)).replace("\\", "/").strip(".")
        out[(rel + "/").replace("//", "/")] = p.read_text(encoding="utf-8", errors="replace")
    return out


def _text(html: str) -> str:
    """태그·스크립트 제거한 본문 텍스트(공백 유지)."""
    body = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body))


def _canonical(html: str) -> str:
    m = re.search(r'rel="canonical"[^>]+href="([^"]+)"', html, re.I)
    return m.group(1).strip() if m else ""


def _is_noindex(html: str) -> bool:
    return bool(re.search(r'name="robots"[^>]+content="[^"]*noindex', html, re.I))


def audit_internal_links(pages: dict[str, str]) -> list[Finding]:
    """글↔글 내부링크 정합 — 고아(inbound 0)·막다른 글(outbound 0).

    크롤러가 따라오는 건 inbound다. sitemap에만 있고 어느 글도 안 가리키면 크롤 우선순위가
    바닥으로 떨어진다. 렌더 경로가 둘(category.html 재사용 / article.html 폴백)이라 코드가
    아니라 **산출물**을 본다 — 한쪽만 고쳐도 통과하던 함정 차단.
    """
    arts = {u: h for u, h in pages.items() if u.startswith("/articles/")}
    if len(arts) < 2:
        return []
    slugs = {u.strip("/").split("/")[-1]: u for u in arts}
    inbound = dict.fromkeys(slugs, 0)
    out: list[Finding] = []
    for url, html in arts.items():
        me = url.strip("/").split("/")[-1]
        linked = {s for s in re.findall(r'href="/articles/([^/"]+)/"', html) if s != me}
        if not linked:
            out.append(Finding("fail", "link-dead-end", f"{url} 다른 글로 나가는 링크 0"))
        for s in linked:
            if s in inbound:
                inbound[s] += 1
    for slug, n in sorted(inbound.items()):
        if n == 0:
            out.append(
                Finding("fail", "link-orphan", f"{slugs[slug]} 어느 글도 가리키지 않음(고아)")
            )
    return out


def audit_onpage(pages: dict[str, str]) -> list[Finding]:
    """온페이지 SEO — title·canonical·H1·og:image·JSON-LD·제휴링크 rel. noindex는 제외."""
    out: list[Finding] = []
    titles: dict[str, list[str]] = {}
    for url, h in sorted(pages.items()):
        if _is_noindex(h):
            continue  # 색인 대상이 아니면 온페이지 품질을 따질 의미가 없다
        t = re.search(r"<title>(.*?)</title>", h, re.I | re.S)
        tv = t.group(1).strip() if t else ""
        if not tv:
            out.append(Finding("fail", "title-missing", f"{url} title 없음"))
        else:
            titles.setdefault(tv, []).append(url)
        if not _canonical(h).startswith("https://"):
            out.append(Finding("fail", "canonical-missing", f"{url} canonical 없음"))
        n_h1 = len(re.findall(r"<h1[^>]*>", h, re.I))
        if n_h1 != 1:
            out.append(Finding("fail", "h1-count", f"{url} H1 {n_h1}개(정확히 1개여야 함)"))
        if not re.search(r'property="og:image"', h, re.I):
            out.append(Finding("fail", "og-image", f"{url} og:image 없음(공유 카드 이미지 누락)"))
        if not re.search(r'name="description"[^>]+content="[^"]+"', h, re.I):
            out.append(Finding("warn", "description-missing", f"{url} meta description 없음"))
        for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
            try:
                json.loads(raw)
            except json.JSONDecodeError:
                out.append(Finding("fail", "jsonld-broken", f"{url} JSON-LD 파싱 실패"))
        if url.startswith("/articles/"):
            for typ in ("Article", "BreadcrumbList"):
                if f'"{typ}"' not in h:
                    out.append(Finding("fail", "jsonld-missing", f"{url} {typ} 스키마 없음"))
        for a in re.findall(r'<a\b[^>]*href="/go/[^"]*"[^>]*>', h, re.I):
            rel = re.search(r'rel="([^"]*)"', a)
            if not rel or not {"nofollow", "sponsored"} & set(rel.group(1).split()):
                out.append(
                    Finding("fail", "affiliate-rel", f"{url} 제휴링크 rel nofollow/sponsored 없음")
                )
                break
    # 제목이 같아도 한쪽이 다른 쪽을 canonical로 가리키면 구글이 통합한다 = 정상(#51 /personas/
    # 오탐). 둘 다 자기 자신을 가리킬 때만 진짜 중복. 정확 일치로 비교(부분일치는 '/'가 아무
    # 슬래시 끝 canonical에나 걸린다).
    for tv, urls in titles.items():
        selfc = [u for u in urls if _canonical(pages[u]) == f"{SITE_ORIGIN}{u}"]
        if len(selfc) > 1:
            out.append(Finding("fail", "title-duplicate", f"title 중복 {selfc}: {tv[:40]}"))
    return out


def audit_sitemap(site: Path, pages: dict[str, str]) -> list[Finding]:
    """sitemap ↔ 산출물 정합. sitemap이 없는 URL을 가리키면 크롤러가 404를 먹는다."""
    sm = site / "sitemap.xml"
    if not sm.exists():
        return [Finding("fail", "sitemap-missing", "sitemap.xml 없음")]
    locs = set(re.findall(r"<loc>([^<]+)</loc>", sm.read_text(encoding="utf-8", errors="replace")))
    want = {f"{SITE_ORIGIN}{u}" for u, h in pages.items() if not _is_noindex(h)}
    out = [
        Finding("fail", "sitemap-404", f"sitemap에 있으나 산출물 없음: {e}")
        for e in sorted(locs - want)
    ]
    out += [Finding("warn", "sitemap-gap", f"sitemap 누락: {m}") for m in sorted(want - locs)]
    return out


def audit_compliance(pages: dict[str, str]) -> list[Finding]:
    """공정위 대가성 고지 (위반 시 쿠팡 30일 수익 몰수·CLAUDE.md §9).

    제휴 링크가 있는 페이지는 대가성 문구가 있어야 한다. 5게이트의 disclosure는 **생성 시점**의
    본문을 보는데, 템플릿이 바뀌어 렌더에서 문구가 빠지면 못 잡는다. 그래서 최종 산출물에서
    한 번 더 본다(수익이 걸린 문제라 fail-closed).

    ★'첫머리' 요건은 **추천 글(/articles/)에만** 적용한다 — 공정위 심사지침은 게시물의 첫
    부분 **또는 끝 부분**을 허용하고, 프로젝트 규칙(§9-4)의 첫머리 고지도 추천 콘텐츠 대상이다.
    홈·카테고리 인덱스는 추천 게시물이 아니라 목록이라 푸터 고지로 충분하다.
    ※이 구분을 안 두면 홈이 매일 걸려 **무인 배포가 영구히 막힌다**(#51 게이트 도입 전 실측으로
      적발 — 과민 게이트가 발행을 죽이는 #48 실패를 그대로 재현할 뻔했다).
    """
    out: list[Finding] = []
    for url, h in sorted(pages.items()):
        if "/go/" not in h:
            continue  # 제휴 링크 없는 페이지는 고지 의무 없음
        text = _text(h)
        if not any(k in text for k in _DISCLOSURE_TERMS):
            out.append(Finding("fail", "disclosure-missing", f"{url} 대가성 고지 문구 없음"))
        elif url.startswith("/articles/") and not any(
            k in text[:_DISCLOSURE_HEAD_CHARS] for k in _DISCLOSURE_TERMS
        ):
            out.append(Finding("fail", "disclosure-late", f"{url} 대가성 고지가 첫머리에 없음"))
    return out


def audit_duplication(pages: dict[str, str]) -> list[Finding]:
    """글 본문 유사도 — 키워드만 바꾼 양산 의심 (구글 Helpful Content).

    차단하지 않는다(warn). 같은 카테고리 글은 구조·상품 카탈로그를 공유해 어느 정도 겹치는
    게 정상이고, 어느 선부터 페널티인지 확정된 근거가 없다. 급증을 **보이게** 하는 게 목적.
    """
    arts = sorted(
        (u, _text(h)[:_SIMILARITY_SAMPLE]) for u, h in pages.items() if u.startswith("/articles/")
    )
    out: list[Finding] = []
    for i, (ua, ta) in enumerate(arts):
        for ub, tb in arts[i + 1 :]:
            r = difflib.SequenceMatcher(None, ta, tb).ratio()
            if r >= _SIMILARITY_WARN:
                out.append(Finding("warn", "content-similar", f"본문 유사도 {r:.2f}: {ua} ↔ {ub}"))
    return out


def audit_site(site: Path) -> list[Finding]:
    """배포 산출물 전수 감사. 산출물이 없으면 빈 목록(빌드 전 — 게이트를 막지 않는다·§0).

    반환 순서 = fail 먼저. 호출부는 has_failures()로 차단 여부를 판단한다.
    """
    if not (site / "index.html").is_file():
        return []
    pages = _pages(site)
    found = (
        audit_internal_links(pages)
        + audit_onpage(pages)
        + audit_sitemap(site, pages)
        + audit_compliance(pages)
        + audit_duplication(pages)
    )
    return sorted(found, key=lambda f: (f.severity != "fail", f.code, f.message))


def has_failures(findings: list[Finding]) -> bool:
    return any(f.severity == "fail" for f in findings)


def summarize(findings: list[Finding], limit: int = 6) -> str:
    """알림·로그용 한 덩어리 요약 — 텔레그램 메시지에 그대로 넣는다."""
    fails = [f for f in findings if f.severity == "fail"]
    warns = [f for f in findings if f.severity != "fail"]
    lines = [f"결함 {len(fails)}건 · 경고 {len(warns)}건"]
    for f in fails[:limit]:
        lines.append(f"  [결함] {f.message}")
    if len(fails) > limit:
        lines.append(f"  … 결함 외 {len(fails)-limit}건")
    for f in warns[:2]:
        lines.append(f"  [경고] {f.message}")
    if len(warns) > 2:
        lines.append(f"  … 경고 외 {len(warns)-2}건")
    return "\n".join(lines)
