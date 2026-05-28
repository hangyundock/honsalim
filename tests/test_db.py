"""common.db 회귀 테스트 — connect·migrate·seed·db_stats.

출처: DB.md §14·§15-1 + BACKEND §9 [확정].
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

try:
    import pytest
except ImportError:
    pytest = None  # type: ignore[assignment]

from common import db

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = PROJECT_ROOT / "sql" / "migrations"
SEEDS_DIR = PROJECT_ROOT / "sql" / "seeds"


def _temp_db() -> Path:
    """OS 임시 폴더에 빈 DB 경로 — 명시적 삭제 필요."""
    fd, path = tempfile.mkstemp(suffix=".db", prefix="honsalim_test_")
    os.close(fd)
    os.unlink(path)  # connect()가 생성하도록 빈 경로만
    return Path(path)


def _cleanup(path: Path) -> None:
    """WAL 모드 부산물 포함 정리."""
    for suffix in ("", "-wal", "-shm", "-journal"):
        p = Path(str(path) + suffix)
        if p.exists():
            try:
                p.unlink()
            except OSError:
                pass


class TestConnect:
    def test_creates_db_file(self) -> None:
        path = _temp_db()
        try:
            conn = db.connect(path)
            conn.close()
            assert path.exists()
        finally:
            _cleanup(path)

    def test_pragmas_applied(self) -> None:
        path = _temp_db()
        try:
            conn = db.connect(path)
            # WAL 모드 확인
            mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
            assert str(mode).lower() == "wal"
            # foreign_keys ON
            fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
            assert int(fk) == 1
            conn.close()
        finally:
            _cleanup(path)


class TestMigrationDiscovery:
    def test_finds_001(self) -> None:
        files = db.discover_migrations(MIGRATIONS_DIR)
        assert len(files) >= 1
        assert files[0].version == 1
        assert files[0].name == "001_initial_schema.sql"

    def test_sorted_by_version(self) -> None:
        files = db.discover_migrations(MIGRATIONS_DIR)
        versions = [f.version for f in files]
        assert versions == sorted(versions)


class TestMigrate:
    def test_current_version_empty_db_is_zero(self) -> None:
        path = _temp_db()
        try:
            conn = db.connect(path)
            assert db.current_version(conn) == 0
            conn.close()
        finally:
            _cleanup(path)

    def test_dry_run_returns_pending_without_applying(self) -> None:
        path = _temp_db()
        try:
            pending = db.migrate(db_path=path, dry_run=True)
            assert len(pending) >= 1
            # dry_run 후에도 schema_version 미생성
            conn = db.connect(path)
            assert db.current_version(conn) == 0
            conn.close()
        finally:
            _cleanup(path)

    def test_migrate_applies_schema_and_updates_version(self) -> None:
        path = _temp_db()
        try:
            applied = db.migrate(db_path=path)
            assert len(applied) >= 1
            conn = db.connect(path)
            assert db.current_version(conn) == 1
            # 13 핵심 테이블 생성 확인
            tables = {
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            for required in ("personas", "scenarios", "drafts", "articles", "schema_version"):
                assert required in tables
            conn.close()
        finally:
            _cleanup(path)

    def test_migrate_idempotent_second_run_empty(self) -> None:
        path = _temp_db()
        try:
            db.migrate(db_path=path)  # 첫 적용
            applied = db.migrate(db_path=path)  # 두 번째
            assert applied == []  # 미적용 없음
        finally:
            _cleanup(path)


class TestSeed:
    def test_seed_populates_personas_and_scenarios(self) -> None:
        path = _temp_db()
        try:
            db.migrate(db_path=path)
            db.seed(db_path=path)
            stats = db.db_stats(db_path=path)
            assert stats["personas"] == 3
            assert stats["scenarios"] == 10
        finally:
            _cleanup(path)

    def test_seed_idempotent_via_insert_or_ignore(self) -> None:
        path = _temp_db()
        try:
            db.migrate(db_path=path)
            db.seed(db_path=path)
            db.seed(db_path=path)  # 두 번째 실행
            stats = db.db_stats(db_path=path)
            assert stats["personas"] == 3  # 중복 없음
            assert stats["scenarios"] == 10
        finally:
            _cleanup(path)


class TestDbStats:
    def test_empty_db_returns_negative(self) -> None:
        path = _temp_db()
        try:
            db.connect(path).close()  # 빈 파일 생성 (테이블 없음)
            stats = db.db_stats(db_path=path)
            # 테이블 없으면 -1
            assert stats["personas"] == -1
        finally:
            _cleanup(path)

    def test_missing_file_returns_empty(self) -> None:
        path = _temp_db()
        # 파일 만들지 않고 호출
        stats = db.db_stats(db_path=path)
        assert stats == {}


if __name__ == "__main__":
    if pytest is not None:
        pytest.main([__file__, "-v"])
