"""dashboard.preview_server — 미리보기 로컬 HTTP 서빙 (세션 #34).

file://로 미리보기를 열면 절대경로 자원(/static/css·js·이미지)이 디스크 루트로 해석돼 무스타일·
레이아웃 깨짐(EVENTS #30 한계 — 실제 화면과 전혀 다르게 보임). 로컬 HTTP 서버(빌드 디렉토리
루트)로 서빙하면 절대경로가 정상 해석돼 라이브 사이트와 동일하게 보인다.

- 127.0.0.1 전용 바인딩(외부 비노출·보안) + OS 할당 임의 포트.
- 백그라운드 데몬 스레드 — 대시보드 프로세스 생존 동안 유지, 종료 시 함께 사라짐(정리 불필요).
- 같은 디렉토리는 기존 서버 재사용(빌드 갱신해도 파일을 매 요청 읽으므로 재기동 불필요).
- PyQt 비의존(테스트 가능) — 순수 stdlib(http.server·threading).
"""

from __future__ import annotations

import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

_server: ThreadingHTTPServer | None = None
_served_dir: str | None = None
_lock = threading.Lock()


class _QuietHandler(SimpleHTTPRequestHandler):
    """요청 로그 억제 — 대시보드 콘솔(실행 로그) 오염 방지."""

    def log_message(self, *args: object) -> None:
        return


def serve(directory: Path | str) -> str:
    """directory를 127.0.0.1 로컬 HTTP로 서빙하고 base URL 반환 (http://127.0.0.1:PORT).

    같은 디렉토리를 이미 서빙 중이면 그 서버를 재사용한다(중복 기동 방지). 백그라운드 데몬
    스레드라 대시보드가 살아있는 동안 유지되고 종료 시 함께 사라진다.
    """
    global _server, _served_dir
    target = str(Path(directory).resolve())
    with _lock:
        if _server is not None and _served_dir == target:
            return f"http://127.0.0.1:{_server.server_address[1]}"
        handler = partial(_QuietHandler, directory=target)
        srv = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        _server = srv
        _served_dir = target
        return f"http://127.0.0.1:{srv.server_address[1]}"


def url_for(directory: Path | str, file_path: Path) -> str:
    """서빙 중인 directory 기준 file_path(html)의 브라우저 URL(디렉토리 인덱스로 끝맺음).

    file_path가 .../index.html이면 부모 디렉토리 URL을 반환(서버가 index.html 자동 서빙) —
    절대경로 자원이 정상 해석되도록 항상 HTTP로 연다. directory 밖 경로면 base만 반환(안전).
    """
    base = serve(directory)
    root = Path(directory).resolve()
    parent = file_path.resolve().parent
    try:
        rel = parent.relative_to(root).as_posix()
    except ValueError:
        rel = ""
    return f"{base}/" if rel in ("", ".") else f"{base}/{rel}/"
