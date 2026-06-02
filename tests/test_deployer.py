"""deployer 회귀 — git_push · wrangler_deploy · verify_deploy.

dry_run 모드 우선 — 외부 실호출 없이 명령 빌드·인자 검증.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

try:
    import pytest

    raises = pytest.raises
except ImportError:
    pytest = None  # type: ignore[assignment]

    @contextmanager
    def raises(exc_type: type[BaseException]) -> Any:  # type: ignore[no-redef]
        try:
            yield
        except exc_type:
            return
        raise AssertionError(f"expected {exc_type.__name__}")


from deployer import git_push, verify_deploy, wrangler_deploy

# ─── git_push ─────────────────────────────────────────────────────────


class TestGitPush:
    def test_dry_run_default(self) -> None:
        result = git_push()
        assert result.dry_run is True
        assert result.returncode == 0
        assert "git push origin main" in result.stdout

    def test_custom_remote_branch(self) -> None:
        result = git_push(remote="upstream", branch="dev")
        assert result.command == ["git", "push", "upstream", "dev"]

    def test_command_includes_push(self) -> None:
        result = git_push()
        assert result.command[0] == "git"
        assert "push" in result.command

    def test_empty_remote_raises(self) -> None:
        with raises(ValueError):
            git_push(remote="")

    def test_empty_branch_raises(self) -> None:
        with raises(ValueError):
            git_push(branch="")


# ─── wrangler_deploy ──────────────────────────────────────────────────


class TestWranglerDeploy:
    def test_dry_run_default(self) -> None:
        result = wrangler_deploy()
        assert result.dry_run is True
        assert result.returncode == 0
        assert "wrangler pages deploy" in result.stdout

    def test_command_structure(self) -> None:
        result = wrangler_deploy()
        assert result.command[:3] == ["wrangler", "pages", "deploy"]
        assert "--project-name" in result.command
        assert "honsalim" in result.command

    def test_custom_build_dir_and_project(self) -> None:
        result = wrangler_deploy(build_dir="dist", project_name="my-proj")
        assert "dist" in result.command
        assert "my-proj" in result.command

    def test_empty_build_dir_raises(self) -> None:
        with raises(ValueError):
            wrangler_deploy(build_dir="")

    def test_empty_project_raises(self) -> None:
        with raises(ValueError):
            wrangler_deploy(project_name="")


# ─── verify_deploy ────────────────────────────────────────────────────


class TestVerifyDeploy:
    def test_dry_run_returns_ok(self) -> None:
        result = verify_deploy("https://honsallim.com/", dry_run=True)
        assert result.ok is True
        assert result.status_code is None
        assert result.url == "https://honsallim.com/"
        assert result.error is not None and "DRY" in result.error

    def test_empty_url_raises(self) -> None:
        with raises(ValueError):
            verify_deploy("", dry_run=True)

    def test_invalid_url_scheme_raises(self) -> None:
        with raises(ValueError):
            verify_deploy("honsallim.com", dry_run=True)
        with raises(ValueError):
            verify_deploy("ftp://x", dry_run=True)

    def test_http_url_accepted(self) -> None:
        result = verify_deploy("http://localhost:8000/", dry_run=True)
        assert result.url == "http://localhost:8000/"


if __name__ == "__main__":
    if pytest is not None:
        pytest.main([__file__, "-v"])
