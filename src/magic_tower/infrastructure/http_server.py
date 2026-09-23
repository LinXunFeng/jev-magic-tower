from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from magic_tower.application.game_service import GameService
from magic_tower.application.settings import JevSettings
from magic_tower.domain.rules import IllegalMove


class GameHttpServer(ThreadingHTTPServer):
    def __init__(
        self,
        address: tuple[str, int],
        service: GameService,
        settings: JevSettings,
        static_dir: Path,
    ) -> None:
        super().__init__(address, GameRequestHandler)
        self.service = service
        self.settings = settings
        self.static_dir = static_dir


class GameRequestHandler(BaseHTTPRequestHandler):
    server: GameHttpServer

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/state":
            language = parse_qs(parsed.query).get("lang", ["zh"])[0]
            self._json(HTTPStatus.OK, self.server.service.snapshot(language))
            return
        if path == "/api/config":
            self._json(HTTPStatus.OK, self.server.settings.public_snapshot())
            return
        self._serve_static(path)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            payload = self._read_json()
            language = str(payload.get("lang", "zh"))
            if path == "/api/move":
                result = self.server.service.move(str(payload.get("action_id", "")), language)
            elif path == "/api/ai/step":
                result = self.server.service.ai_step(str(payload.get("mode", "jev")), language)
            elif path == "/api/reset":
                result = self.server.service.reset(language)
            elif path == "/api/config":
                if payload.get("action") == "reset":
                    result = self.server.settings.reset_to_environment()
                else:
                    result = self.server.settings.configure(
                        api_key=str(payload.get("api_key", "")),
                        base_url=str(payload.get("base_url", "")),
                        model=str(payload.get("model", "")),
                    )
            else:
                self._json(HTTPStatus.NOT_FOUND, {"error": "Route not found"})
                return
            self._json(HTTPStatus.OK, result)
        except (IllegalMove, ValueError) as exc:
            self._json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        # The delivery boundary must turn unexpected adapter failures into JSON
        # without killing the threaded server.
        except Exception as exc:  # noqa: BLE001
            self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[web] {self.address_string()} - {format % args}")

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _json(self, status: HTTPStatus, data: Any) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self, request_path: str) -> None:
        relative = "index.html" if request_path == "/" else request_path.lstrip("/")
        target = (self.server.static_dir / relative).resolve()
        static_root = self.server.static_dir.resolve()
        if static_root not in target.parents and target != static_root:
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        if not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        content = target.read_bytes()
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)
