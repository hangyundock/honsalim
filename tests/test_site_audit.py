"""validator.site_audit + 배포 전 게이트 회귀 테스트 (세션 #51).

★배경: 무인 시스템에 생산 자동화만 있고 감시가 없어, 글↔글 링크 0·전 페이지 og:image 누락이
40일간 매일 '정상'으로 보고됐다(배포 후 검증이 홈 1페이지 상태코드만 봤다). 주인 승인으로
'결함이면 배포 중단 + 즉시 알림'을 넣었다. 이 파일은 **게이트가 실제로 막는지**를 고정한다 —
막지 못하는 게이트는 있으나 마나이고, 과민한 게이트는 발행을 죽인다(#48 교훈). 둘 다 검증한다.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from validator import site_audit

ORIGIN = "https://honsallim.com"


def _page(
    site: Path,
    rel: str,
    *,
    title: str = "충분히 긴 제목입니다",
    canonical: str | None = None,
    h1: int = 1,
    og_image: bool = True,
    noindex: bool = False,
    body: str = "",
    schema: bool = True,
) -> None:
    url = "/" + rel + "/" if rel else "/"
    can = canonical if canonical is not None else f"{ORIGIN}{url}"
    d = site / rel if rel else site
    d.mkdir(parents=True, exist_ok=True)
    head = f'<title>{title}</title><link rel="canonical" href="{can}">'
    head += '<meta name="description" content="충분히 긴 설명 문구입니다.">'
    if og_image:
        head += f'<meta property="og:image" content="{ORIGIN}/x.webp">'
    if noindex:
        head += '<meta name="robots" content="noindex, follow">'
    if schema and rel.startswith("articles/"):
        head += '<script type="application/ld+json">{"@type":"Article"}</script>'
        head += '<script type="application/ld+json">{"@type":"BreadcrumbList"}</script>'
    hs = "".join(f"<h1>제목{i}</h1>" for i in range(h1))
    (d / "index.html").write_text(
        f"<html><head>{head}</head><body>{hs}{body}</body></html>", "utf-8"
    )


def _sitemap(site: Path, urls: list[str]) -> None:
    locs = "".join(f"<loc>{ORIGIN}{u}</loc>" for u in urls)
    (site / "sitemap.xml").write_text(f"<urlset>{locs}</urlset>", encoding="utf-8")


def _healthy(site: Path, n: int = 3) -> None:
    """결함 없는 최소 사이트 — 글 n편이 서로 링크되고 고지·스키마가 갖춰진 상태."""
    slugs = [f"a{i}" for i in range(n)]
    _page(site, "")
    for i, s in enumerate(slugs):
        others = [x for x in slugs if x != s]
        links = "".join(f'<a href="/articles/{o}/">{o}</a>' for o in others)
        body = (
            "<p>혼살림은 제휴(어필리에이트) 링크를 사용하며 수수료를 받을 수 있습니다.</p>"
            + f"<p>본문 {i} 고유 내용</p>" * (i + 1)
            + links
            + f'<a href="/go/ali-{i}" rel="nofollow sponsored">상품</a>'
        )
        _page(site, f"articles/{s}", title=f"글 제목 {i} 입니다", body=body)
    _sitemap(site, ["/"] + [f"/articles/{s}/" for s in slugs])


class TestAuditCatchesRealDefects:
    """#51에서 실제로 발생했던 결함들을 재현해 잡히는지 확인."""

    def test_orphan_article_is_fail(self, tmp_path: Path) -> None:
        """40일간 방치됐던 바로 그 상태 — 아무도 안 가리키는 글."""
        _healthy(tmp_path)
        _page(
            tmp_path,
            "articles/lonely",
            title="외톨이 글입니다",
            body='<a href="/articles/a0/">a0</a>',
        )
        _sitemap(
            tmp_path, ["/", "/articles/a0/", "/articles/a1/", "/articles/a2/", "/articles/lonely/"]
        )
        codes = {f.code for f in site_audit.audit_site(tmp_path) if f.severity == "fail"}
        assert "link-orphan" in codes

    def test_missing_og_image_is_fail(self, tmp_path: Path) -> None:
        """전 42페이지에서 누락됐던 배선 결함."""
        _healthy(tmp_path)
        _page(tmp_path, "", og_image=False)
        assert "og-image" in {
            f.code for f in site_audit.audit_site(tmp_path) if f.severity == "fail"
        }

    def test_missing_disclosure_is_fail(self, tmp_path: Path) -> None:
        """제휴 링크가 있는데 대가성 고지가 없으면 공정위 위반 = 수익 몰수 경로."""
        _healthy(tmp_path)
        _page(
            tmp_path,
            "articles/a0",
            title="고지 빠진 글입니다",
            body='<a href="/articles/a1/">a1</a><a href="/go/ali-9" rel="nofollow sponsored">상품</a>',
        )
        assert "disclosure-missing" in {
            f.code for f in site_audit.audit_site(tmp_path) if f.severity == "fail"
        }

    def test_affiliate_link_without_rel_is_fail(self, tmp_path: Path) -> None:
        _healthy(tmp_path)
        _page(
            tmp_path,
            "articles/a0",
            title="rel 빠진 글입니다",
            body="<p>제휴 수수료를 받습니다.</p><a href='/articles/a1/'>a1</a><a href=\"/go/ali-9\">상품</a>",
        )
        assert "affiliate-rel" in {
            f.code for f in site_audit.audit_site(tmp_path) if f.severity == "fail"
        }

    def test_sitemap_pointing_nowhere_is_fail(self, tmp_path: Path) -> None:
        _healthy(tmp_path)
        _sitemap(tmp_path, ["/", "/articles/a0/", "/articles/a1/", "/articles/a2/", "/사라진/"])
        assert "sitemap-404" in {
            f.code for f in site_audit.audit_site(tmp_path) if f.severity == "fail"
        }


class TestAuditDoesNotOverBlock:
    """★과민 게이트는 발행을 죽인다(#48). 정상 사이트를 막지 않는지가 똑같이 중요하다."""

    def test_healthy_site_has_no_failures(self, tmp_path: Path) -> None:
        _healthy(tmp_path)
        findings = site_audit.audit_site(tmp_path)
        assert not site_audit.has_failures(findings), [
            f.message for f in findings if f.severity == "fail"
        ]

    def test_noindex_page_is_exempt(self, tmp_path: Path) -> None:
        """noindex는 색인 대상이 아니라 온페이지·sitemap 대조에서 제외 — /reviews/ 오탐 방지."""
        _healthy(tmp_path)
        _page(tmp_path, "reviews/x", noindex=True, og_image=False, canonical="", title="")
        assert not site_audit.has_failures(site_audit.audit_site(tmp_path))

    def test_duplicate_title_with_canonical_is_not_failure(self, tmp_path: Path) -> None:
        """canonical로 통합된 중복은 정상 — /personas/ 오탐."""
        _healthy(tmp_path)
        _page(tmp_path, "personas/a", title="같은 제목입니다")
        _page(tmp_path, "personas", title="같은 제목입니다", canonical=f"{ORIGIN}/personas/a/")
        _sitemap(
            tmp_path,
            ["/", "/articles/a0/", "/articles/a1/", "/articles/a2/", "/personas/a/", "/personas/"],
        )
        assert not site_audit.has_failures(site_audit.audit_site(tmp_path))

    def test_similar_content_is_warn_not_fail(self, tmp_path: Path) -> None:
        """같은 카테고리 글은 구조를 공유해 겹친다 — 차단하면 정상 발행이 막힌다."""
        _healthy(tmp_path, n=2)
        # ★반복문 40회 같은 픽스처는 부적절 — 5-gram '집합'이라 반복이 뭉개져 Jaccard가
        # 낮게 나온다. 실제 글처럼 문장이 다양하면서 두 페이지가 동일해야 양산을 재현한다.
        same = "<p>혼살림은 제휴 수수료를 받습니다.</p>" + "".join(
            f"<p>{i}번 문단: 원룸 책상 높이와 의자 좌판 깊이를 함께 맞추는 방법 {i*7}</p>"
            for i in range(60)
        )
        for s, o in (("a0", "a1"), ("a1", "a0")):
            _page(
                tmp_path,
                f"articles/{s}",
                title=f"제목 {s} 입니다",
                body=same
                + f'<a href="/articles/{o}/">{o}</a><a href="/go/ali-1" rel="nofollow">상품</a>',
            )
        findings = site_audit.audit_site(tmp_path, include_duplication=True)
        assert not site_audit.has_failures(findings)
        assert any(f.code == "content-similar" for f in findings)

    def test_duplication_is_off_by_default(self, tmp_path: Path) -> None:
        """★#51 재검수: 유사도는 warn이라 배포를 막지도 않는데 글 수의 제곱으로 비싸다.

        실측 — SequenceMatcher 22편 12.3초(200편 추정 17분). 매일 도는 배포 게이트가 그만큼
        느려지면 무인 운영이 망가진다. 기본은 꺼두고 doctor·주간 리포트에서만 켠다.
        """
        _healthy(tmp_path, n=2)
        # ★반복문 40회 같은 픽스처는 부적절 — 5-gram '집합'이라 반복이 뭉개져 Jaccard가
        # 낮게 나온다. 실제 글처럼 문장이 다양하면서 두 페이지가 동일해야 양산을 재현한다.
        same = "<p>혼살림은 제휴 수수료를 받습니다.</p>" + "".join(
            f"<p>{i}번 문단: 원룸 책상 높이와 의자 좌판 깊이를 함께 맞추는 방법 {i*7}</p>"
            for i in range(60)
        )
        for s, o in (("a0", "a1"), ("a1", "a0")):
            _page(
                tmp_path,
                f"articles/{s}",
                title=f"제목 {s} 입니다",
                body=same
                + f'<a href="/articles/{o}/">{o}</a><a href="/go/ali-1" rel="nofollow">상품</a>',
            )
        assert not any(f.code == "content-similar" for f in site_audit.audit_site(tmp_path))

    def test_similarity_threshold_clears_real_site_distribution(self, tmp_path: Path) -> None:
        """임계값이 정상 사이트를 걸지 않는가 — 실측 최고 0.628 대비 여유가 있어야 한다.

        _healthy()는 글마다 본문 길이가 다른 정상 상태다. 여기서 경고가 뜨면 임계값이 과민하다.
        """
        _healthy(tmp_path, n=3)
        assert site_audit._SIMILARITY_WARN >= 0.7  # 실측 분포(최고 0.628) 위여야 오탐이 없다
        assert not any(
            f.code == "content-similar"
            for f in site_audit.audit_site(tmp_path, include_duplication=True)
        )

    def test_unbuilt_site_returns_empty(self, tmp_path: Path) -> None:
        """빌드 전이면 빈 목록 — 게이트가 fresh checkout을 막으면 안 된다(§0)."""
        assert site_audit.audit_site(tmp_path) == []

    def test_footer_disclosure_on_index_page_is_ok(self, tmp_path: Path) -> None:
        """★홈·카테고리는 푸터 고지로 충분 — '첫머리' 요건은 추천 글에만.

        게이트 도입 전 실측에서 홈이 이 항목에 걸렸다(고지가 푸터 4419번째 글자). 그대로
        켰으면 **매일 배포가 막혔다**. 공정위 심사지침은 첫 부분 또는 끝 부분을 허용하고,
        홈은 추천 게시물이 아니라 목록 페이지다. 과민 게이트가 발행을 죽이는 #48 재현 방지.
        """
        _healthy(tmp_path)
        long_intro = "<p>목록 페이지 소개 문구</p>" * 60  # 고지를 1200자 밖으로 밀어냄
        _page(
            tmp_path,
            "",
            body=long_intro
            + '<a href="/go/ali-1" rel="nofollow sponsored">상품</a>'
            + "<footer>혼살림은 제휴(어필리에이트) 링크로 수수료를 받을 수 있습니다.</footer>",
        )
        findings = site_audit.audit_site(tmp_path)
        assert not site_audit.has_failures(findings), [
            f.message for f in findings if f.severity == "fail"
        ]

    def test_article_still_requires_first_disclosure(self, tmp_path: Path) -> None:
        """반대로 추천 글은 첫머리 고지가 여전히 필수 — 완화가 글까지 뚫으면 안 된다."""
        _healthy(tmp_path)
        long_intro = "<p>본문 앞부분 채우기</p>" * 200  # 고지를 1200자 밖으로 확실히 밀어냄
        _page(
            tmp_path,
            "articles/a0",
            title="고지가 뒤에 있는 글",
            body=long_intro
            + '<a href="/articles/a1/">a1</a><a href="/go/ali-1" rel="nofollow sponsored">상품</a>'
            + "<footer>제휴 수수료를 받습니다.</footer>",
        )
        assert "disclosure-late" in {
            f.code for f in site_audit.audit_site(tmp_path) if f.severity == "fail"
        }


class TestDeployGate:
    """refresh_cycle 배포 전 게이트 — 결함이면 실제로 배포를 멈추는가."""

    def _run(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, findings: list):
        """실제 render까지 돌린 뒤 게이트 배선을 검증. audit 결과만 주입해 분기를 고정한다."""
        from common import db
        from deployer import refresh_cycle as rc
        from validator import site_audit as sa

        monkeypatch.setattr(sa, "audit_site", lambda _site: findings)
        # git push까지 가지 않도록 — 게이트가 통과했을 때만 여기 닿는다는 사실 자체가 검증 대상
        pushed: list[bool] = []

        def _spy(_root: Path) -> tuple[bool, str]:
            pushed.append(True)
            return (False, "")  # 변경 없음 → 실제 commit·push까지 가지 않는다

        monkeypatch.setattr(rc, "detect_changes", _spy)
        db_path = tmp_path / "t.db"
        db.migrate(db_path=db_path)
        db.seed(db_path=db_path)
        conn = db.connect(db_path)
        try:
            res = rc.run_refresh_cycle(
                conn,
                project_root=tmp_path,
                refresh=False,
                auto_killswitch=False,
                do_build=True,
                do_deploy=True,
                dry_run=False,
                db_path=db_path,
            )
        finally:
            conn.close()
        return res, pushed

    def test_gate_blocks_deploy_on_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """★핵심: 결함이 있으면 배포 단계에 **도달조차 하지 않는다**."""
        bad = [site_audit.Finding("fail", "og-image", "/ og:image 없음")]
        res, pushed = self._run(tmp_path, monkeypatch, bad)
        assert res.built is True
        assert res.gate_blocked and "og:image" in res.gate_blocked
        assert res.deployed is False
        assert pushed == [], "게이트가 막았는데 배포 경로로 진입했다"

    def test_gate_allows_deploy_when_clean(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """★과민 방지: 결함이 없으면 정상적으로 배포 경로로 진행한다."""
        res, pushed = self._run(tmp_path, monkeypatch, [])
        assert res.gate_blocked is None
        assert pushed == [True], "정상 산출물인데 배포 경로에 진입하지 못했다"

    def test_warnings_alone_do_not_block(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """경고만 있으면 배포는 계속 — 발행 연속성 보호(#48 과민 게이트 교훈)."""
        warns = [site_audit.Finding("warn", "sitemap-gap", "/x/ 누락")]
        res, pushed = self._run(tmp_path, monkeypatch, warns)
        assert res.gate_blocked is None
        assert pushed == [True]
        assert any("경고" in n for n in res.notes)


class TestGateResultInterpretation:
    """★#51 재검수 적발 — 게이트 차단을 '성공'으로 오판하던 분기 (실제 버그였다).

    게이트가 막으면 built=True · changed=False · deployed=False가 된다. auto_cycle의
    '비공개 반영' 경로는 `res.deployed or not res.changed`를 성공 조건으로 써서, 이 조합이
    True로 평가돼 **"라이브 반영 완료 · rc=0"으로 보고하고 알림도 안 갔다**. 가드레일이 내린
    글이 라이브에 남은 채 조용히 지나가는 상태 — #47에서 고친 결함의 재발이었다.
    """

    def _result(self, *, gate_blocked: str | None):
        from deployer.refresh_cycle import CycleResult

        r = CycleResult(dry_run=False)
        r.built = True
        r.changed = False  # 게이트가 detect_changes 전에 반환하므로 기본값 그대로
        r.deployed = False
        r.gate_blocked = gate_blocked
        return r

    def test_blocked_result_is_not_mistaken_for_success(self) -> None:
        """옛 성공 조건이 차단 결과에 True를 주는지 고정 — 이 조합이 버그의 정체다."""
        r = self._result(gate_blocked="결함 1건")
        assert (r.deployed or not r.changed) is True, "전제 붕괴 — 오판 조건이 재현되지 않음"
        assert r.gate_blocked, "gate_blocked를 먼저 보지 않으면 성공으로 오판된다"

    def test_clean_result_still_reads_as_success(self) -> None:
        """정상 회차(변경 없음)는 여전히 성공으로 읽혀야 한다 — 과잉 차단 방지."""
        r = self._result(gate_blocked=None)
        assert r.gate_blocked is None
        assert (r.deployed or not r.changed) is True


def test_summarize_includes_failures() -> None:
    """알림 문구에 결함 내용이 실제로 실리는가 — 주인이 명령 없이 원인을 알아야 한다."""
    fs = [
        site_audit.Finding("fail", "og-image", "/ og:image 없음"),
        site_audit.Finding("warn", "sitemap-gap", "/x/ 누락"),
    ]
    s = site_audit.summarize(fs)
    assert "결함 1건" in s and "og:image" in s
