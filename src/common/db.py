"""혼살림 SQLite 연결·마이그레이션.

출처: DB.md §14·§15-1 [확정] + ARCH §3 [확정] + BACKEND §9 (db migrate 명령).

핵심:
- 연결 시 PRAGMA 4종 자동 적용 (DB §15-1: WAL·NORMAL·foreign_keys·MEMORY)
- 마이그레이션: sql/migrations/*.sql 파일명 첫 숫자 = version
- schema_version 테이블에서 MAX 조회 후 미적용분 순차 실행 (DB §14-3)
- 실패 시 ROLLBACK + 예외 (DB §14-3)
- dry-run 지원 (DB §14-4)
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "honsalim.db"
MIGRATIONS_DIR = PROJECT_ROOT / "sql" / "migrations"
SEEDS_DIR = PROJECT_ROOT / "sql" / "seeds"

# DB §15-1 PRAGMA — 연결 시 자동 적용
PRAGMAS = (
    "PRAGMA journal_mode = WAL",
    "PRAGMA synchronous = NORMAL",
    "PRAGMA foreign_keys = ON",
    "PRAGMA temp_store = MEMORY",
)

# 파일명 패턴: 001_xxx.sql · 002_yyy.sql ...
_VERSION_PREFIX_RE = re.compile(r"^(\d+)_")


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """SQLite 연결 + PRAGMA 적용.

    isolation_level 기본값(deferred) 사용 — executescript 또는 명시 COMMIT 호환.
    """
    db_path.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    for pragma in PRAGMAS:
        conn.execute(pragma)
    return conn


def current_version(conn: sqlite3.Connection) -> int:
    """schema_version의 MAX(version) 반환. 테이블 없으면 0."""
    try:
        row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        return int(row[0]) if row and row[0] is not None else 0
    except sqlite3.OperationalError:
        # 테이블 미존재 (최초 마이그레이션 전)
        return 0


@dataclass(frozen=True)
class MigrationFile:
    version: int
    path: Path

    @property
    def name(self) -> str:
        return self.path.name


def discover_migrations(migrations_dir: Path = MIGRATIONS_DIR) -> list[MigrationFile]:
    """sql/migrations/*.sql 정렬·파싱."""
    if not migrations_dir.exists():
        return []
    files: list[MigrationFile] = []
    for sql_path in sorted(migrations_dir.glob("*.sql")):
        m = _VERSION_PREFIX_RE.match(sql_path.stem)
        if not m:
            continue
        files.append(MigrationFile(version=int(m.group(1)), path=sql_path))
    return files


def pending_migrations(
    conn: sqlite3.Connection, migrations_dir: Path = MIGRATIONS_DIR
) -> list[MigrationFile]:
    """현재 schema_version 이후 미적용 마이그레이션 목록."""
    cur = current_version(conn)
    return [m for m in discover_migrations(migrations_dir) if m.version > cur]


def apply_migration(conn: sqlite3.Connection, migration: MigrationFile) -> None:
    """단일 .sql 파일을 적용. executescript는 내부적으로 트랜잭션 처리.

    실패 시 sqlite3가 자동 ROLLBACK + 예외 전파.
    """
    sql = migration.path.read_text(encoding="utf-8")
    try:
        conn.executescript(sql)
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def migrate(
    db_path: Path = DB_PATH,
    migrations_dir: Path = MIGRATIONS_DIR,
    dry_run: bool = False,
) -> list[MigrationFile]:
    """미적용 마이그레이션을 순차 적용. dry-run 시 목록만 반환.

    반환: 적용된 (또는 dry-run에서 적용될) 마이그레이션 목록.
    """
    conn = connect(db_path)
    try:
        pending = pending_migrations(conn, migrations_dir)
        if dry_run:
            return pending
        for m in pending:
            apply_migration(conn, m)
        return pending
    finally:
        conn.close()


def seed(
    db_path: Path = DB_PATH,
    seeds_dir: Path = SEEDS_DIR,
    dry_run: bool = False,
) -> list[Path]:
    """sql/seeds/*.sql 적용. INSERT OR IGNORE 가정 — idempotent.

    seed는 schema_version 추적 안 함 — 단순 반복 실행 가능 (INSERT OR IGNORE).
    """
    if not seeds_dir.exists():
        return []
    seed_files = sorted(seeds_dir.glob("*.sql"))
    if dry_run:
        return seed_files
    conn = connect(db_path)
    try:
        for f in seed_files:
            sql = f.read_text(encoding="utf-8")
            try:
                conn.executescript(sql)
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return seed_files
    finally:
        conn.close()


def db_stats(db_path: Path = DB_PATH) -> dict[str, int]:
    """주요 테이블 row count. 데이터 진척 가시화용."""
    if not db_path.exists():
        return {}
    conn = connect(db_path)
    try:
        stats: dict[str, int] = {}
        for table in ("personas", "scenarios", "products", "drafts", "articles"):
            try:
                # table 이름은 코드 내 화이트리스트 — SQL injection 아님
                row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()  # noqa: S608
                stats[table] = int(row[0]) if row else 0
            except sqlite3.OperationalError:
                # 테이블 미존재 — 마이그레이션 전
                stats[table] = -1
        return stats
    finally:
        conn.close()
