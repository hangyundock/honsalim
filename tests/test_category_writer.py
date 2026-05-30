"""category_writer 회귀 테스트 (세션 #15) — 프롬프트 조립·dry_run. 라이브 호출 없음.

출처: BACKEND §8-1.
"""

from __future__ import annotations

from enricher import build_category_prompt, generate_category_guide
from enricher.claude_client import ClaudeClient

SEO = {"primary": "컴퓨터 책상", "secondary": ["게이밍책상", "서재책상", "철제책상"]}


class TestBuildPrompt:
    def test_includes_category_and_directive(self) -> None:
        p = build_category_prompt("컴퓨터 책상", SEO)
        assert "컴퓨터 책상" in p
        assert "SEO 키워드 배치" in p  # 2층 배치 지시 주입됨
        assert "게이밍책상" in p  # 보조키워드 노출
        assert "1인칭" in p  # 진실성 규칙

    def test_feedback_appended(self) -> None:
        p = build_category_prompt("컴퓨터 책상", SEO, feedback=["density_low: 밀도 부족"])
        assert "보완" in p
        assert "density_low" in p


class TestDryRun:
    def test_dry_run_no_api_call(self) -> None:
        client = ClaudeClient(api_key=None)  # 키 없어도 dry_run OK
        res = generate_category_guide(client, "컴퓨터 책상", SEO, dry_run=True)
        assert res.dry_run is True
        assert res.response_text is None
        assert "컴퓨터 책상" in res.user_prompt
        assert len(res.system_blocks) == 1  # 카테고리 system 1블록


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
