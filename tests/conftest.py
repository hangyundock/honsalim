"""pytest 공통 설정 — src/ 모듈을 import 가능하게 sys.path 보정."""

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
