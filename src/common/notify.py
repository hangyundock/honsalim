"""common.notify — 텔레그램 푸시 알림 (세션 #41, EVENTS #39 '푸시 채널' 이월 과제).

무인 운영 중 대시보드는 안 열리므로(#39), 사람 조치가 필요한 순간(쿠팡 첨부 소진 임박·
게이트 반려 상한·발행 0편 위험)과 일일 결과를 주인 휴대폰으로 밀어 보낸다.

원칙(§0):
- **절대 사이클을 죽이지 않는다** — 모든 실패(미설정·네트워크·API 오류)는 False 반환+로그만.
- secrets는 `D:\\secrets\\affiliate_hub\\telegram.env` (TELEGRAM_BOT_TOKEN·TELEGRAM_CHAT_ID) —
  config.load_secrets()가 폴더의 *.env를 전부 로드하므로 파일만 두면 자동 인식.
  미설정이면 조용히 무동작(기존 파일/로그 자기보고는 그대로 1차 채널).
- 표준 라이브러리만 사용(urllib) — 의존성 추가 없음.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

_API = "https://api.telegram.org/bot{token}/sendMessage"
_TIMEOUT_S = 10  # 무인 사이클을 오래 붙잡지 않도록 짧게
_MAX_LEN = 3800  # 텔레그램 상한 4096 — 여유를 두고 자름(잘림 표시 포함)


def telegram_ready() -> bool:
    """토큰·챗ID 환경변수가 둘 다 있으면 True. 호출 전 config.load_secrets() 필요."""
    return bool(os.environ.get("TELEGRAM_BOT_TOKEN")) and bool(os.environ.get("TELEGRAM_CHAT_ID"))


def send_telegram(text: str) -> bool:
    """텔레그램으로 text 발송. 성공 True / 실패·미설정 False (예외 절대 전파 안 함·§0).

    HTML/Markdown 파싱 미사용(plain text) — 제목의 특수문자로 API 400이 나는 함정 회피.
    """
    if not telegram_ready():
        return False
    body = (text or "").strip()
    if not body:
        return False
    if len(body) > _MAX_LEN:
        body = body[:_MAX_LEN] + "\n…(잘림)"
    try:
        token = os.environ["TELEGRAM_BOT_TOKEN"]
        payload = json.dumps(
            {
                "chat_id": os.environ["TELEGRAM_CHAT_ID"],
                "text": body,
                "disable_web_page_preview": True,
            }
        ).encode("utf-8")
        req = urllib.request.Request(  # noqa: S310 — URL은 코드 고정 https 템플릿(변수는 토큰뿐)
            _API.format(token=token),
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:  # noqa: S310 — https 고정
            ok = bool(json.loads(resp.read().decode("utf-8")).get("ok"))
        if not ok:
            print("[notify] 텔레그램 API가 ok=false 반환 — 토큰/챗ID 확인 필요(발송 생략)")
        return ok
    except (urllib.error.URLError, OSError, ValueError, KeyError) as e:
        # 네트워크·API 오류는 무인 사이클에 치명적이지 않다 — 로그만 남기고 계속(§0 격리).
        print(f"[notify] 텔레그램 발송 실패(무시하고 계속): {type(e).__name__}: {e}")
        return False
