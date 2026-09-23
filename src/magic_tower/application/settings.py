from __future__ import annotations

import os
from dataclasses import dataclass
from threading import RLock
from typing import Any


@dataclass(frozen=True, slots=True)
class JevConfiguration:
    api_key: str
    base_url: str
    model: str


class JevSettings:
    """Runtime Jev configuration with environment values as immutable defaults."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._environment = JevConfiguration(
            api_key=os.getenv("TYPESAFE_API_KEY", ""),
            base_url=os.getenv("TYPESAFE_BASE_URL", "https://api.typesafe.ai"),
            model=os.getenv("TYPESAFE_MODEL", "jev-latest"),
        )
        self._override: JevConfiguration | None = None

    def current(self) -> JevConfiguration:
        with self._lock:
            return self._override or self._environment

    def configure(self, api_key: str, base_url: str, model: str) -> dict[str, Any]:
        with self._lock:
            current = self._override or self._environment
            resolved_key = api_key.strip() or current.api_key
            resolved_url = base_url.strip() or current.base_url
            resolved_model = model.strip() or current.model
            if not resolved_url.startswith(("http://", "https://")):
                raise ValueError("API 地址必须以 http:// 或 https:// 开头")
            if not resolved_model:
                raise ValueError("模型名称不能为空")
            self._override = JevConfiguration(resolved_key, resolved_url.rstrip("/"), resolved_model)
            return self.public_snapshot()

    def reset_to_environment(self) -> dict[str, Any]:
        with self._lock:
            self._override = None
            return self.public_snapshot()

    def public_snapshot(self) -> dict[str, Any]:
        with self._lock:
            current = self._override or self._environment
            return {
                "configured": bool(current.api_key),
                "source": "page" if self._override else "environment",
                "base_url": current.base_url,
                "model": current.model,
                "api_key_hint": self._key_hint(current.api_key),
            }

    @staticmethod
    def _key_hint(api_key: str) -> str:
        if not api_key:
            return "未配置"
        if len(api_key) <= 8:
            return "••••••••"
        return f"{api_key[:3]}••••{api_key[-4:]}"

