"""scripts/deploy_go_gateway.py — /go/ 게이트웨이 인프라 배포 (세션 #21).

무인 운영 골격: Cloudflare D1 테이블 생성(멱등) + published 제품 slug_map UPSERT +
go_gateway.js Workers 배포. CLOUDFLARE_API_TOKEN은 CF_API_TOKEN(secrets)에서 매핑(미출력).
각 단계 실패 시 명확히 보고하고 중단(무인 가시화). 멱등이라 재실행 안전.

실행: PYTHONPATH=src python scripts/deploy_go_gateway.py
"""

from __future__ import annotations

import os
import subprocess
import sys

sys.path.insert(0, "src")

from common import config, db
from common.proc import resolve_argv
from tracker import slug_map


def _run(cmd: list[str], label: str, timeout: int = 150) -> None:
    print(f"\n=== {label} ===")
    r = subprocess.run(  # noqa: S603
        resolve_argv(cmd), capture_output=True, text=True, timeout=timeout
    )
    out = (r.stdout + r.stderr).strip()
    print(out[-1000:])
    if r.returncode != 0:
        print(f"[FAIL] {label} rc={r.returncode}")
        sys.exit(2)
    print(f"[OK] {label}")


def main() -> int:
    config.load_secrets()
    tok = os.environ.get("CF_API_TOKEN")
    if not tok:
        print("[FAIL] CF_API_TOKEN 없음 — secrets 확인")
        return 1
    os.environ["CLOUDFLARE_API_TOKEN"] = tok
    os.environ["CLOUDFLARE_ACCOUNT_ID"] = os.environ.get("CF_ACCOUNT_ID", "")

    # 1. 인증 확인 (토큰 값 미출력 — whoami는 계정 정보만)
    _run(["wrangler", "whoami"], "wrangler 인증 확인")

    # 2. D1 스키마 (slug_map·clicks·clicks_daily, CREATE IF NOT EXISTS 멱등)
    _run(
        [
            "wrangler",
            "d1",
            "execute",
            "honsalim-clicks",
            "--remote",
            "--file",
            "sql/d1/schema.sql",
            "-y",
        ],
        "D1 스키마 적용",
    )

    # 3. slug_map UPSERT (published article·카테고리 제품)
    conn = db.connect(db.DB_PATH)
    try:
        res = slug_map.sync_slug_map(conn, dry_run=False)
    finally:
        conn.close()
    print(f"\n=== slug_map 동기화 === {len(res.entries)} slug")
    if res.error:
        print(f"[FAIL] {res.error}\n{(res.stderr or '')[-600:]}")
        return 3
    print("[OK] slug_map UPSERT")

    # 4. Workers 배포 (go_gateway.js → honsalim.com/go/*)
    _run(["wrangler", "deploy"], "Workers 배포 (go_gateway.js)")

    print("\n=== /go/ 인프라 배포 완료 ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
