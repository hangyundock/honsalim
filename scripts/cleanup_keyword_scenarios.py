"""cleanup_keyword_scenarios.py — 키워드 파생 가짜 시나리오 정리 + 흡수 글 비공개 (세션 #35).

배경: 키워드→글 생성이 '내맘대로 세팅'에 가짜 시나리오 카드를 자동 생성해 페이지를 오염시켰고,
카테고리와 중복되는 키워드 글(노트북받침대 ≈ 모니터받침대 카테고리)이 라이브 고아 페이지로 남았다.
코드는 #35에서 근본 수정(키워드 시나리오 active=0 생성·키워드 삭제 시 시나리오 동반 삭제·중복 글
301 리다이렉트)했고, 이 스크립트는 '이미 쌓인' 운영 DB junk를 일회성으로 정리한다.

안전(§0): 실행 전 DB를 백업하고, 멱등(재실행해도 무해)하며, 식별 규칙은 검증된 일반 규칙
(priority=0 = 키워드 파생 — 실 시나리오는 모두 priority>0)을 쓴다. Claude는 운영 DB를 직접
수정하지 않으므로(#32 가드) 주인이 런처(.bat)로 직접 실행한다.

실행 후: 대시보드에서 '🚀 빌드·배포'를 눌러 라이브 반영(세팅 junk 카드 사라지고, 노트북받침대
글 URL은 모니터받침대 카테고리로 301).
"""

from __future__ import annotations

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "honsalim.db"
# 카테고리로 흡수돼 비공개할 글 슬러그(코드의 REDIRECTS와 일치) — 노트북받침대 → monitor-stand
ABSORBED_SLUGS = ("kw-4d525971",)


def main() -> int:
    if not DB.exists():
        print(f"[ERR] DB not found: {DB}")
        return 1

    # 1) 백업 (sqlite backup API — 일관 스냅샷)
    bdir = ROOT / "data" / "backups"
    bdir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = bdir / f"honsalim_before_cleanup_{ts}.db"

    conn = sqlite3.connect(str(DB))
    try:
        bconn = sqlite3.connect(str(backup))
        conn.backup(bconn)
        bconn.close()
        print(f"[OK] backup -> data/backups/{backup.name}")

        # 2) 키워드 파생 가짜 시나리오 비활성 (priority=0 = 키워드 파생, 실 시나리오는 priority>0)
        n_scen = conn.execute(
            "SELECT COUNT(*) FROM scenarios WHERE priority=0 AND active=1"
        ).fetchone()[0]
        conn.execute("UPDATE scenarios SET active=0 WHERE priority=0 AND active=1")
        print(f"[OK] deactivated keyword-derived scenarios: {n_scen}")

        # 3) 카테고리로 흡수된 중복 글 비공개 (빌드에서 페이지 미생성 -> _redirects 301 적용).
        #    published_at=NULL 동반 — CHECK 제약(status!='published'이면 published_at NULL) 충족.
        #    WHERE status='published'라 재실행해도 무해(멱등).
        now = datetime.now().isoformat(timespec="seconds")
        n_art = 0
        for slug in ABSORBED_SLUGS:
            n_art += conn.execute(
                "UPDATE articles SET status='unpublished', published_at=NULL, updated_at=? "
                "WHERE slug=? AND status='published'",
                (now, slug),
            ).rowcount
        print(f"[OK] unpublished absorbed articles: {n_art}")

        conn.commit()

        # 4) 결과 리포트
        act = conn.execute("SELECT COUNT(*) FROM scenarios WHERE active=1").fetchone()[0]
        pub = conn.execute("SELECT COUNT(*) FROM articles WHERE status='published'").fetchone()[0]
        print(f"[DONE] active scenarios now={act}, published articles now={pub}")
        print("Next: open dashboard -> click '빌드·배포' to deploy to honsallim.com")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
