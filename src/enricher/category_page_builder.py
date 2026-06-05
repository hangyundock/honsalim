"""category_page_builder — 카테고리 페이지 콘텐츠 빌드 오케스트레이션 (세션 #17).

생성(category_writer) → SEO 게이트 통과까지 재생성(seo_regenerate, 비용 상한) →
disclosure 삽입 → 진실성 게이트(truth·disclosure·links) → 구조화 콘텐츠 DB 저장.

사무용 의자 프로토타입 구성을 표준으로: 도입·타입 비교표·체크리스트·흔한 실수·
추천 6선(+타입)·제품명 기반 비교표·FAQ. (신뢰박스·전체 카탈로그는 렌더러가 결합)

가격 정확성은 카탈로그(DB 직접)가 담당 → truth 가격검증은 산문 제외(products=[]).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from collector import product_filter, seo_keywords
from enricher import category_writer
from validator import disclosure as disc_gate
from validator import links as links_gate
from validator import truth
from validator.seo import check_seo
from writer import article_writer

# 개념 이미지 저장 위치 — renderer가 static/ 전체를 build/site/static/로 복사(배포 경로 동일)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONCEPT_IMG_DIR = _PROJECT_ROOT / "static" / "images" / "concepts"

_PRODUCTS_SQL = """
    SELECT p.id, p.deeplink_slug AS slug, p.name, p.price_krw, cp.tier,
           p.sales_volume, p.evaluate_rate, p.discount_pct
    FROM category_products cp
    JOIN products p ON p.id = cp.product_id
    WHERE cp.category_id = ?
    ORDER BY CASE cp.tier WHEN 'budget' THEN 0 WHEN 'premium' THEN 1 ELSE 2 END,
             cp.display_order, p.id
"""

# 추천 6선 선정(세션 #19) — 긍정 피드백율 하한(%). 명백히 낮은 제품만 제외하는 '품질 floor'.
# ★80%: 실측에서 90%는 과도했다 — 판매량 71·만족도 89.3%인 베스트셀러가 0.7% 차로 탈락하고
#   판매량 2~6개(리뷰 2~3개라 '100%'는 무의미)가 추천되는 역전 발생. 80 미만(명백한 저품질)만 거른다.
_SATISFACTION_FLOOR = 80.0

# status는 'draft' 고정 — AI 자동 published 금지(§2-마·E7). 공개는 사용자 승인(approve-category)만.
# 재빌드(콘텐츠 변경) 시에도 draft로 되돌려 재승인을 강제한다(미승인 변경 노출 방지).
_SAVE_GUIDE_SQL = """
    UPDATE categories
    SET guide_title = ?, guide_md = ?, content_json = ?, faq_json = ?,
        guide_generated_at = CURRENT_TIMESTAMP, status = 'draft'
    WHERE id = ?
"""

# ★세션 #24 가드: 6선 리셋은 **알리 채널 한정**. 쿠팡 수동 적재분(source='coupang')은 별도
#   채널이라 알리 재빌드가 pick_reason(쿠팡 노트) 등을 지우면 안 됨 → source='aliexpress'만.
_RESET_FEATURED_SQL = """
    UPDATE category_products
    SET is_featured = 0, pros_json = NULL, cons_json = NULL, pick_reason = NULL, pick_type = NULL
    WHERE category_id = ?
      AND product_id IN (SELECT id FROM products WHERE source = 'aliexpress')
"""

_SET_PICK_SQL = """
    UPDATE category_products
    SET is_featured = 1, tier = ?, pros_json = ?, cons_json = ?, pick_reason = ?, pick_type = ?
    WHERE category_id = ? AND product_id = (SELECT id FROM products WHERE deeplink_slug = ?)
"""


def _page_sources(conn: sqlite3.Connection, category_id: int) -> set[str]:
    """첫머리 고지용 제휴처 집합 — 카테고리에 쿠팡 상품이 연결돼 있으면 'coupang' 추가(세션 #24).

    카테고리 페이지는 알리 카탈로그가 기본이라 'aliexpress'는 항상 포함. 쿠팡 수동 적재분
    (collector.coupang)이 연결돼 있으면 첫머리에 '쿠팡 파트너스'도 명시(공정위 정확성·disclosure 게이트).
    """
    srcs = {"aliexpress"}
    if conn.execute(
        "SELECT 1 FROM category_products cp JOIN products p ON p.id = cp.product_id "
        "WHERE cp.category_id = ? AND p.source = 'coupang' LIMIT 1",
        (category_id,),
    ).fetchone():
        srcs.add("coupang")
    return srcs


def load_products(conn: sqlite3.Connection, category_id: int) -> list[dict[str, Any]]:
    """카테고리 연결 제품 → 프롬프트 주입용 dict(slug·name·price·tier)."""
    rows = conn.execute(_PRODUCTS_SQL, (category_id,)).fetchall()
    out: list[dict[str, Any]] = []
    for r in rows:
        price = r["price_krw"]
        out.append(
            {
                "id": r["id"],
                "slug": r["slug"],
                "name": r["name"],
                "price": f"{price:,}원" if price else "",
                "tier": r["tier"],
                "volume": r["sales_volume"],  # 알리 최근 판매량 — 추천 선정 순위
                "rate": r["evaluate_rate"],  # 긍정 피드백율 % — 선정 하한 필터
                "discount_pct": r["discount_pct"],  # 신뢰 할인율 동률 tiebreak
            }
        )
    return out


def select_featured(products: list[dict[str, Any]], per_tier: int = 3) -> list[dict[str, Any]]:
    """추천 6선 자동 선정 (세션 #19) — 투명·재현 규칙. AI는 선정에 관여하지 않는다.

    티어(실속/고급)별로 **항상 per_tier개를 채우되**, 정렬 우선순위로 품질을 반영한다:
      정렬키 = (만족도 명백한 저평가 아님, 판매량 내림차순, 신뢰 할인율).
      → ① 만족도 80% 이상/없음(0·None) 제품이 ② 명백한 저평가(0<rate<80) 제품보다 항상 앞.
      → 같은 등급 안에서는 판매량 많은 순. 저평가 제품은 '맨 뒤'라 6개를 채우려 부족할 때만 들어온다.
    반환: [{slug, tier, name, volume}] (티어별 per_tier개, 제품이 그만큼 있으면, budget→premium 순).

    설계 근거(실측 보정·세션 #19): 추천 수가 6개로 항상 차도록(주인 요구) 하되, 만족도 낮은 제품은
    뒤로 밀어 가급적 노출 안 한다. 만족도는 알리에서 절반만 제공·신상품은 0이므로 '없음'은 통과로
    본다(부당 제외 방지). 하한 90%는 89%대 베스트셀러를 떨궈 80%로 보정(세션 #19 실측).
    """

    def _vol(p: dict[str, Any]) -> int:
        return int(p.get("volume") or 0)

    def _disc(p: dict[str, Any]) -> int:
        return product_filter.trusted_discount(p.get("discount_pct")) or 0

    def _is_poor(p: dict[str, Any]) -> bool:
        # 명백한 저평가: 만족도가 '있고'(0/None=피드백 없음 제외) 0<rate<80. 이런 제품만 뒤로 민다.
        r = p.get("rate")
        return r is not None and 0 < float(r) < _SATISFACTION_FLOOR

    chosen: list[dict[str, Any]] = []
    for tier in ("budget", "premium"):
        pool = [p for p in products if p.get("tier") == tier]
        # 저평가 아님 → 판매량 → 할인율 순(reverse). 저평가 제품은 맨 뒤라 자리가 모자랄 때만 선정됨.
        ranked = sorted(pool, key=lambda p: (not _is_poor(p), _vol(p), _disc(p)), reverse=True)
        chosen += [
            {"slug": p["slug"], "tier": tier, "name": p["name"], "volume": _vol(p)}
            for p in ranked[:per_tier]
        ]
    return chosen


def _prose(parsed: dict[str, Any], primary: str = "") -> str:
    """SEO 측정·진실성 게이트용 산문 합본.

    소제목(##/###)으로 구조화 — seo 게이트의 '소제목 내 대표키워드' 항목 충족용.
    primary가 있으면 대표키워드를 포함한 소제목을 1개 둔다.
    """
    parts: list[str] = [parsed.get("lead", ""), parsed.get("guide_intro", "")]
    if primary:
        parts.append(f"## {primary} 핵심 체크포인트")
    parts += [f"### {c['title']}\n{c['why']}" for c in parsed.get("checkpoints", [])]
    if parsed.get("mistakes"):
        parts.append(f"## 흔한 실수\n{parsed['mistakes']}")
    parts += [f"### {f['q']}\n{f['a']}" for f in parsed.get("faq", [])]
    return "\n\n".join(p for p in parts if p)


def _run_gates(guide_md: str) -> tuple[bool, dict[str, Any]]:
    """truth(1인칭·AI흔적·과장)·disclosure·links 게이트. 가격검증은 산문 제외(products=[])."""
    ok_t, rep_t = truth.check_truth({"body_md": guide_md, "products": []})
    ok_d, rep_d = disc_gate.check_disclosure(guide_md)
    ok_l, rep_l = links_gate.check_links(guide_md)
    gates = {
        "truth": {"pass": ok_t, "issues": rep_t.get("issues", [])},
        "disclosure": {"pass": ok_d, "issues": rep_d.get("issues", [])},
        "links": {"pass": ok_l, "issues": rep_l.get("issues", [])},
    }
    return (ok_t and ok_d and ok_l), gates


def _save(
    conn: sqlite3.Connection, category_id: int, parsed: dict[str, Any], guide_md: str
) -> None:
    """구조화 콘텐츠(content_json)·산문(guide_md)·FAQ + 추천 6선(pros/cons/이유/타입) 저장(멱등)."""
    content = {
        "lead": parsed.get("lead", ""),
        "guide_intro": parsed.get("guide_intro", ""),
        "type_table": parsed.get("type_table", []),
        "checkpoints": parsed.get("checkpoints", []),
        "mistakes": parsed.get("mistakes", ""),
        "compare": parsed.get("compare", {"rows": [], "cells": []}),
    }
    conn.execute(
        _SAVE_GUIDE_SQL,
        (
            parsed["title"],
            guide_md,
            json.dumps(content, ensure_ascii=False),
            json.dumps(parsed.get("faq", []), ensure_ascii=False),
            category_id,
        ),
    )
    conn.execute(_RESET_FEATURED_SQL, (category_id,))  # 이전 6선 해제 후 재설정
    for pk in parsed.get("picks", []):
        conn.execute(
            _SET_PICK_SQL,
            (
                pk["tier"],
                json.dumps(pk["pros"], ensure_ascii=False),
                json.dumps(pk["cons"], ensure_ascii=False),
                pk["for"],
                pk.get("type", ""),
                category_id,
                pk["slug"],
            ),
        )
    conn.commit()


def build_and_save(
    conn: sqlite3.Connection,
    slug: str,
    client: Any,
    *,
    dry_run: bool = True,
    require_gates: bool = True,
    max_attempts: int = 2,
    generate_image: bool = True,
) -> dict[str, Any]:
    """카테고리 콘텐츠 생성·SEO 재생성·검증·저장 + 개념 이미지 생성.

    dry_run=True: 제품 로드 + 프롬프트 길이만(HTTP·DB 쓰기 없음).
    dry_run=False: SEO 게이트 통과까지 재생성(상한 max_attempts) → disclosure → truth/disclosure/links
                   게이트 → (통과 시) 구조화 콘텐츠 저장. SEO 미달은 저장하되 리포트로 가시화.
    generate_image=True: 글 저장 후 Imagen으로 개념 이미지 1장 생성(~$0.02). 실패해도 글은 유지.
    """
    conn.row_factory = sqlite3.Row
    cat = conn.execute("SELECT id, name_ko FROM categories WHERE slug = ?", (slug,)).fetchone()
    if cat is None:
        raise KeyError(f"categories에 {slug!r} 없음 — db seed 필요")
    category_id, cat_name = int(cat[0]), cat[1]
    products = load_products(conn, category_id)
    if not products:
        raise ValueError(f"{slug}: 연결된 제품 없음 — 먼저 카테고리 수집 필요")

    seo_cfg = seo_keywords.gate_config(slug)
    # 추천 6선 = 판매량 기준 결정적 선정(세션 #19). AI는 이 6개의 '설명'만 작성한다.
    selected = select_featured(products)

    if dry_run:
        prompt = category_writer.build_category_page_prompt(
            cat_name, products, seo_cfg, selected=selected
        )
        return {
            "dry_run": True,
            "products": len(products),
            "selected": len(selected),
            "prompt_len": len(prompt),
        }

    # picks는 선정된 6개 slug로 제한(AI가 다른 제품을 추천에 넣지 못하게)
    valid = {s["slug"] for s in selected}
    primary = (seo_cfg or {}).get("primary", "")

    # SEO + 진실성(truth·disclosure·links) 통합 게이트를 통과할 때까지 재생성(상한 max_attempts).
    # 1인칭 등 truth 미달도 issues를 피드백으로 다시 생성 — 자가복원(§0). 비용 상한은 tistory 교훈.
    feedback: list[str] | None = None
    final: dict[str, Any] = {}
    last_parse_error: str | None = None
    for attempt in range(1, max(1, max_attempts) + 1):
        try:
            res = category_writer.generate_category_page(
                client,
                cat_name,
                products,
                seo=seo_cfg,
                feedback=feedback,
                selected=selected,
                dry_run=False,
            )
            parsed = category_writer.parse_category_page_response(
                res.response_text, valid_slugs=valid
            )
        except (category_writer.CategoryPageError, RuntimeError) as ex:
            # 자가복원(§0): JSON 파싱 실패 + LLM 호출/응답 오류(타임아웃·응답 잘림·일시적 API)를
            # 모두 재생성으로 흡수 — 전체 중단 방지(무인 안전). 영속 오류는 상한 소진 후 명확히 보고.
            last_parse_error = str(ex)
            feedback = [
                f"직전 생성이 실패했습니다({ex}). "
                "코드펜스·설명문 없이 순수 JSON 객체 하나만 출력하고, 후행 콤마를 넣지 마세요."
            ]
            continue
        last_parse_error = None
        prose = _prose(parsed, primary)
        guide_md = article_writer.apply_disclosure(prose, sources=_page_sources(conn, category_id))
        safe_ok, gates = _run_gates(guide_md)  # truth·disclosure·links
        if primary:
            seo_ok, seo_rep = check_seo(
                {"body_md": prose, "title": parsed["title"], "seo": seo_cfg}
            )
        else:
            seo_ok, seo_rep = True, {}
        final = {
            "parsed": parsed,
            "guide_md": guide_md,
            "usage": getattr(res, "usage", None),
            "safe_ok": safe_ok,
            "gates": gates,
            "seo_ok": seo_ok,
            "seo_rep": seo_rep,
            "attempt": attempt,
        }
        if safe_ok and seo_ok:
            break
        fb = [i for g in gates.values() if not g["pass"] for i in g["issues"]]
        if not seo_ok:
            fb += seo_rep.get("issues", [])
            # A(세션 #19): 밀도 초과 시 행동 가능한 힌트 — 대표키워드 통째 반복 줄이고 대체 표현
            fb.append(
                f"대표키워드 '{primary}'를 본문에서 통째로 반복하지 말고 '제품'·줄임말·대명사로 "
                "대체해 정확형 밀도를 3% 이내로 낮추세요(과밀=스팸)."
            )
        feedback = fb or None

    if not final:
        # 모든 시도가 파싱 실패 — 명확히 보고하고 중단(저장 안 함, 무인 진단)
        raise category_writer.CategoryPageError(
            f"JSON 파싱 {max(1, max_attempts)}회 모두 실패: {last_parse_error}"
        )

    # 추천 6선 = 결정적 선정(판매량) 고정 + AI가 쓴 설명을 slug로 매칭(세션 #19).
    # → 선정은 규칙(투명·재현), 설명만 AI. AI가 누락/오선택해도 featured는 선정 6개로 강제.
    parsed_final = final["parsed"]
    ai_by_slug = {p["slug"]: p for p in parsed_final.get("picks", [])}
    parsed_final["picks"] = [
        {
            "slug": s["slug"],
            "tier": s["tier"],
            "type": ai_by_slug.get(s["slug"], {}).get("type", ""),
            "pros": ai_by_slug.get(s["slug"], {}).get("pros", []),
            "cons": ai_by_slug.get(s["slug"], {}).get("cons", []),
            "for": ai_by_slug.get(s["slug"], {}).get("for", ""),
        }
        for s in selected
    ]

    parsed = final["parsed"]
    report: dict[str, Any] = {
        "dry_run": False,
        "title": parsed["title"],
        "picks": len(parsed["picks"]),
        "type_table": len(parsed["type_table"]),
        "checkpoints": len(parsed["checkpoints"]),
        "compare_rows": len(parsed["compare"]["rows"]),
        "faq": len(parsed["faq"]),
        "gates": final["gates"],
        "overall_pass": final["safe_ok"],
        "seo_passed": final["seo_ok"],
        "seo_attempts": final["attempt"],
        "seo_density": (final["seo_rep"].get("metrics") or {}).get("density_pct"),
        "usage": final["usage"],
    }
    # 안전 게이트(truth·disclosure·links) 통과 시에만 저장. SEO는 best-effort(미달도 저장+보고).
    if require_gates and not final["safe_ok"]:
        report["saved"] = False
        return report

    _save(conn, category_id, parsed, final["guide_md"])
    report["saved"] = True

    # 개념 이미지 — 게이트 통과·저장 후에만(비용 분리, AutoBlog 교훈). 실패해도 글은 그대로.
    if generate_image and parsed.get("image_prompt"):
        from enricher import concept_image

        try:
            out_path = CONCEPT_IMG_DIR / f"{slug}.webp"
            rel = f"/static/images/concepts/{slug}.webp"
            # 이미 생성된 개념 이미지가 있으면 재사용 — Imagen 비용 절약 + 기존 확정 이미지
            # 보존(랜덤 재생성 퇴행 방지). 재생성 강제는 해당 webp를 먼저 삭제. 세션 #21.
            reused = out_path.exists()
            if reused or concept_image.generate_concept_image(parsed["image_prompt"], out_path):
                conn.execute(
                    "UPDATE categories SET concept_image = ?, concept_image_alt = ? WHERE id = ?",
                    (rel, parsed.get("image_alt", ""), category_id),
                )
                conn.commit()
                report["concept_image"] = rel
                report["concept_image_reused"] = reused
        except Exception as exc:  # 이미지 실패는 글 저장에 영향 없음 — 가시화만
            report["concept_image_error"] = str(exc)[:200]
    return report
