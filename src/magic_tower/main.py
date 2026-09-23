from __future__ import annotations

import os
from pathlib import Path

from magic_tower.application.game_service import GameService
from magic_tower.application.settings import JevSettings
from magic_tower.infrastructure.decision_engines import (
    HeuristicDecisionEngine,
    JevDecisionEngine,
    SafeJevDecisionEngine,
)
from magic_tower.infrastructure.env import load_dotenv
from magic_tower.infrastructure.http_server import GameHttpServer


def build_service(settings: JevSettings | None = None) -> GameService:
    settings = settings or JevSettings()
    baseline = HeuristicDecisionEngine()
    jev = JevDecisionEngine(settings)
    return GameService(SafeJevDecisionEngine(jev, baseline), baseline)


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(project_root / ".env")
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8093"))
    static_dir = Path(__file__).resolve().parent / "web" / "static"
    settings = JevSettings()
    server = GameHttpServer((host, port), build_service(settings), settings, static_dir)
    print(f"Jev Magic Tower is running at http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
