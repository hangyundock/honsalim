"""scripts/gen_persona_images.py — 페르소나 개념 이미지 생성 (Imagen 4 Fast). 세션 #21.

/personas/·/scenarios/ 카드의 빈 placeholder를 실사진으로 채우기 위한 페르소나별
개념 이미지 1장씩. 텍스트·브랜드 없는 컨셉 사진(enricher.concept_image 재사용).
이미 파일이 있으면 건너뜀(비용 절약·재실행 안전 — 무인 자동화 §0).

실행: PYTHONPATH=src python scripts/gen_persona_images.py
GOOGLE_API_KEY는 build-category와 동일하게 config.load_secrets()로 확보.
"""

from __future__ import annotations

from pathlib import Path

from common import config
from enricher import concept_image

OUT_DIR = Path("static/images/concepts")

# 페르소나 slug → 영어 장면 묘사(텍스트·브랜드 없는 컨셉 사진). 파일명은 persona-<slug>.webp.
SPECS = {
    "persona-cheot-jachi": (
        "cozy compact studio apartment of a young adult living alone for the first "
        "time, small functional furniture and a neat single bed, warm welcoming starter home"
    ),
    "persona-minimal-life": (
        "minimalist serene one-room apartment interior, few carefully chosen objects, "
        "calm neutral wood and white tones, lots of clean empty space, natural light"
    ),
    "persona-homeoffice": (
        "bright tidy home office corner in a small apartment, wooden desk with a monitor "
        "and an ergonomic chair, work-from-home setup with a few green plants"
    ),
}


def main() -> int:
    config.load_secrets()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    made = 0
    for slug, desc in SPECS.items():
        out = OUT_DIR / f"{slug}.webp"
        if out.exists():
            print(f"[skip] {slug} (이미 존재 — 재사용)")
            continue
        ok = concept_image.generate_concept_image(desc, out, aspect="4:3")
        print(f"[{'OK' if ok else 'EMPTY'}] {slug} -> {out}")
        made += int(ok)
    print(f"신규 생성 {made}장 / 총 {len(SPECS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
