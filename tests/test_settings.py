"""common.settings 회귀 테스트 — config.json 외부화 (세션 #25).

기본값 병합·견고성(없거나 깨진 파일)·저장/조회 라운드트립.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from common import settings


def _tmp_config() -> Path:
    """테스트용 임시 config 경로 (실제 data/config.json 미접촉)."""
    d = Path(tempfile.mkdtemp(prefix="honsalim_cfg_"))
    return d / "config.json"


class TestLoadDefaults:
    def test_missing_file_returns_defaults(self) -> None:
        p = _tmp_config()
        assert not p.exists()
        cfg = settings.load(p)
        assert cfg["publish_per_day"] == settings.DEFAULTS["publish_per_day"]
        assert cfg["schedule_time"] == "11:00"
        assert cfg["coupang_mode"] == "manual"
        assert cfg["coupang_threshold_krw"] == 150000

    def test_corrupt_file_returns_defaults(self) -> None:
        """깨진 JSON → 기본값(무인 안전 정지 방지 §0)."""
        p = _tmp_config()
        p.write_text("{ this is not json", encoding="utf-8")
        cfg = settings.load(p)
        assert cfg["publish_per_day"] == settings.DEFAULTS["publish_per_day"]

    def test_non_dict_json_returns_defaults(self) -> None:
        p = _tmp_config()
        p.write_text("[1, 2, 3]", encoding="utf-8")
        cfg = settings.load(p)
        assert cfg == settings.DEFAULTS


class TestPartialOverride:
    def test_partial_file_merges_over_defaults(self) -> None:
        """일부 키만 둔 파일 → 나머지는 기본값."""
        p = _tmp_config()
        p.write_text(json.dumps({"publish_per_day": 5}), encoding="utf-8")
        cfg = settings.load(p)
        assert cfg["publish_per_day"] == 5  # override
        assert cfg["schedule_time"] == settings.DEFAULTS["schedule_time"]  # default 유지

    def test_unknown_keys_preserved(self) -> None:
        p = _tmp_config()
        p.write_text(json.dumps({"future_knob": "x"}), encoding="utf-8")
        cfg = settings.load(p)
        assert cfg["future_knob"] == "x"
        assert cfg["featured_per_tier"] == settings.DEFAULTS["featured_per_tier"]


class TestGet:
    def test_get_existing_key(self) -> None:
        p = _tmp_config()
        p.write_text(json.dumps({"featured_per_tier": 4}), encoding="utf-8")
        assert settings.get("featured_per_tier", path=p) == 4

    def test_get_falls_back_to_default(self) -> None:
        p = _tmp_config()
        assert settings.get("satisfaction_floor", path=p) == settings.DEFAULTS["satisfaction_floor"]

    def test_get_unknown_key_returns_supplied_default(self) -> None:
        p = _tmp_config()
        assert settings.get("nonexistent", default=42, path=p) == 42


class TestSaveRoundTrip:
    def test_save_then_load(self) -> None:
        p = _tmp_config()
        settings.save({"publish_per_day": 3, "coupang_mode": "api"}, p)
        assert p.exists()
        cfg = settings.load(p)
        assert cfg["publish_per_day"] == 3
        assert cfg["coupang_mode"] == "api"
        # 저장 안 한 키는 기본값으로 채워짐(병합 저장)
        assert cfg["schedule_time"] == settings.DEFAULTS["schedule_time"]

    def test_save_writes_utf8_readable_json(self) -> None:
        p = _tmp_config()
        settings.save({"notes_label": "한글 설정"}, p)
        loaded = json.loads(p.read_text(encoding="utf-8"))
        assert loaded["notes_label"] == "한글 설정"

    def test_ensure_creates_when_missing(self) -> None:
        p = _tmp_config()
        assert not p.exists()
        out = settings.ensure_config_file(p)
        assert out == p
        assert p.exists()
        assert settings.load(p)["publish_per_day"] == settings.DEFAULTS["publish_per_day"]

    def test_ensure_keeps_existing(self) -> None:
        p = _tmp_config()
        settings.save({"publish_per_day": 9}, p)
        settings.ensure_config_file(p)  # 덮어쓰지 않음
        assert settings.load(p)["publish_per_day"] == 9
