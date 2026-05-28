"""혼살림 로깅 표준.

출처: BACKEND §7 [확정] + ARCH §3 (logs/honsalim.log) [확정].

설계:
- 포맷 (BACKEND §7-1):
    [YYYY-MM-DD HH:MM:SS.fff KST] [모듈명] LEVEL 메시지
- 레벨 (BACKEND §7-2): DEBUG·INFO·WARN·ERROR
- 90일 회전 (BACKEND §7-1, OPS §...)
- 보안 redact (BACKEND §7-4): secrets 값은 절대 로그 출력 금지
"""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "honsalim.log"

# BACKEND §7-1 포맷
LOG_FORMAT = "[%(asctime)s.%(msecs)03d KST] [%(name)s] %(levelname)s %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# BACKEND §7-4: 메시지에 포함되면 안 되는 키 패턴 (방어선)
# 코드 작성 시 secrets 값 자체를 로그에 넣지 않는 게 원칙이지만,
# 실수 방어를 위해 메시지에 이 패턴이 등호 뒤 값과 함께 있으면 마스킹.
SENSITIVE_KEY_PATTERNS = (
    "ANTHROPIC_API_KEY",
    "CF_API_TOKEN",
    "COUPANG_SECRET_KEY",
    "COUPANG_ACCESS_KEY",
    "INDEXNOW_KEY",
    "GH_PAT",
)


class RedactFilter(logging.Filter):
    """secrets 키 패턴이 메시지에 나타나면 값 부분 마스킹.

    완벽한 보호는 아님 — 코드 작성 시 secrets 값 자체를 로그에 넣지 않는 것이 1차 방어.
    본 필터는 실수 시 2차 방어.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        for key in SENSITIVE_KEY_PATTERNS:
            if key in msg:
                # 값 부분 마스킹 — KEY=value 형태 가정
                import re

                msg = re.sub(rf"({key}\s*[=:]\s*)\S+", r"\1***REDACTED***", msg)
        # record.msg를 직접 갱신하면 args 처리에 영향 — args 비우고 msg만 갱신
        record.msg = msg
        record.args = ()
        return True


_configured = False


def setup_logging(level: int = logging.INFO, console: bool = True) -> logging.Logger:
    """루트 로거 1회 설정. 이미 설정됐으면 재설정 안 함.

    반환: 루트 로거.
    """
    global _configured
    root = logging.getLogger()
    if _configured:
        return root

    LOG_DIR.mkdir(exist_ok=True)
    root.setLevel(level)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    redact = RedactFilter()

    # 파일 핸들러 — 일자별 회전 90일 (BACKEND §7-1)
    file_handler = logging.handlers.TimedRotatingFileHandler(
        LOG_FILE,
        when="midnight",
        backupCount=90,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(redact)
    root.addHandler(file_handler)

    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.addFilter(redact)
        root.addHandler(console_handler)

    _configured = True
    return root


def get_logger(name: str) -> logging.Logger:
    """모듈별 로거. 호출 전 setup_logging() 1회 필요."""
    return logging.getLogger(name)
