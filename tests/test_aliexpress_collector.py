"""collector.aliexpress 회귀 테스트 — 서명·요청 빌드·상품 매핑·dry_run.

서명은 AliExpress 공식 "Affiliate API Guidance" FAQ 4.5의 연결 예시와 대조 검증한다.
라이브 HTTP는 호출하지 않는다 (dry_run / 키 미설정 경로만).
"""

from __future__ import annotations

import hashlib
import hmac
from contextlib import contextmanager
from typing import Any

try:
    import pytest

    raises = pytest.raises
except ImportError:  # pragma: no cover
    pytest = None  # type: ignore[assignment]

    @contextmanager
    def raises(exc_type: type[BaseException]) -> Any:  # type: ignore[no-redef]
        try:
            yield
        except exc_type:
            return
        raise AssertionError(f"expected {exc_type.__name__}")


from collector import aliexpress as ali


class TestSign:
    def test_matches_documented_concatenation(self) -> None:
        """FAQ 4.5 order.list 예시의 연결 문자열과 정렬·연결 로직이 일치하는지."""
        params = {
            "app_key": "511111",
            "end_time": "2024-10-29 00:00:00",
            "method": "aliexpress.affiliate.order.list",
            "sign_method": "sha256",
            "start_time": "2024-10-28 00:00:00",
            "status": "Payment Completed",
            "timestamp": "1730710528",
        }
        secret = "test_secret"
        documented_concat = (
            "app_key511111"
            "end_time2024-10-29 00:00:00"
            "methodaliexpress.affiliate.order.list"
            "sign_methodsha256"
            "start_time2024-10-28 00:00:00"
            "statusPayment Completed"
            "timestamp1730710528"
        )
        expected = (
            hmac.new(secret.encode(), documented_concat.encode(), hashlib.sha256)
            .hexdigest()
            .upper()
        )
        assert ali.sign(params, secret) == expected

    def test_excludes_sign_and_empty_values(self) -> None:
        base = {"app_key": "1", "keywords": "lamp"}
        with_extra = {**base, "sign": "OLD", "blank": "", "none": None}
        assert ali.sign(with_extra, "s") == ali.sign(base, "s")

    def test_uppercase_hex_sha256_length(self) -> None:
        out = ali.sign({"app_key": "1"}, "s")
        assert out == out.upper() and len(out) == 64

    def test_md5_supported(self) -> None:
        out = ali.sign({"app_key": "1"}, "s", sign_method="md5")
        assert len(out) == 32 and out == out.upper()

    def test_unknown_method_raises(self) -> None:
        with raises(ValueError):
            ali.sign({"app_key": "1"}, "s", sign_method="rsa")


class TestBuildQueryRequest:
    def test_page_size_cap(self) -> None:
        with raises(ValueError):
            ali.build_query_request("lamp", "k", "t", timestamp=1, page_size=51)

    def test_contains_core_params_and_sign(self) -> None:
        req = ali.build_query_request("스탠드", "APPKEY", "TRACK", timestamp=123, app_secret="sec")
        assert req["method"] == ali.PRODUCT_QUERY
        assert req["app_key"] == "APPKEY"
        assert req["keywords"] == "스탠드"
        assert req["tracking_id"] == "TRACK"
        assert req["target_currency"] == "KRW"
        assert req["sign"] and len(req["sign"]) == 64

    def test_no_secret_leaves_sign_blank(self) -> None:
        req = ali.build_query_request("lamp", "k", "t", timestamp=1)
        assert req["sign"] == ""


class TestMapProduct:
    def test_maps_to_products_schema(self) -> None:
        item = {
            "product_id": "100500",
            "product_title": "LED 스탠드",
            "target_sale_price": "12.34",
            "target_sale_price_currency": "KRW",
            "product_main_image_url": "https://img/x.jpg",
            "promotion_link": "https://s.click.ali/abc",
            "second_level_category_name": "조명",
        }
        row = ali.map_product(item, "TRACK")
        assert row["source"] == "aliexpress"
        assert row["source_product_id"] == "100500"
        assert row["name"] == "LED 스탠드"
        assert row["price_krw"] == 12  # round(12.34)
        assert row["deeplink_url"] == "https://s.click.ali/abc"
        assert row["deeplink_slug"] == "ali-100500"
        assert row["affiliate_tag"] == "TRACK"
        assert row["category_path"] == "조명"

    def test_missing_price_is_none(self) -> None:
        row = ali.map_product({"product_id": "1", "product_title": "x"}, "T")
        assert row["price_krw"] is None


class TestQueryProductsDryRun:
    def test_dry_run_builds_request_without_network(self) -> None:
        res = ali.query_products(
            "원룸 조명",
            timestamp=1730710528,
            dry_run=True,
            app_key="K",
            app_secret="S",
            tracking_id="T",
        )
        assert res.dry_run is True
        assert res.products == []
        assert res.request["keywords"] == "원룸 조명"
        assert res.request["sign"]  # 서명 생성됨

    def test_live_without_keys_raises(self) -> None:
        with raises(RuntimeError):
            ali.query_products(
                "lamp",
                timestamp=1,
                dry_run=False,
                app_key="",
                app_secret="",
                tracking_id="T",
            )
