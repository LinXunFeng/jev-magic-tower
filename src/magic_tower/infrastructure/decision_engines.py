from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from magic_tower.application.i18n import action_description, event_text
from magic_tower.application.ports import Decision
from magic_tower.application.settings import JevSettings
from magic_tower.domain.floors import FLOORS
from magic_tower.domain.models import ActionPreview, GameState, TileKind


class JevUnavailable(RuntimeError):
    pass


class JevDecisionEngine:
    """TypeSafe SDK adapter; it owns all version-dependent integration details."""

    def __init__(
        self,
        settings: JevSettings | None = None,
        client_factory: Callable[[], Any] | None = None,
    ) -> None:
        self._settings = settings or JevSettings()
        self._client_factory = client_factory

    @property
    def configured(self) -> bool:
        return bool(self._settings.current().api_key) or self._client_factory is not None

    def choose(self, state: GameState, candidates: list[ActionPreview]) -> Decision:
        if not self.configured:
            raise JevUnavailable(
                "TYPESAFE_API_KEY is not configured. Choose the local strategy or add it to .env."
            )
        try:
            from typesafe_sdk import Choice, TypeSafeClient
        except ImportError as exc:
            raise JevUnavailable("typesafe-sdk is not installed. Run: pip install -e .") from exc

        criteria = {item.action_id: action_description(item, "en") for item in candidates}
        hero = state.hero
        request_state = {
            "game": "A resource-management dungeon crawler. Reach higher floors and defeat the final boss.",
            "current_floor": f"{state.floor_index + 1}/{len(FLOORS)} {FLOORS[state.floor_index].name}",
            "hero": {
                "hp": hero.hp,
                "attack": hero.attack,
                "defense": hero.defense,
                "gold": hero.gold,
                "yellow_keys": hero.yellow_keys,
                "blue_keys": hero.blue_keys,
            },
            "recent_events": [event_text(item, "en") for item in state.recent_events],
            "turn": state.turn,
            "strategy": (
                "Preserve scarce keys and HP, prefer permanent attack/defense growth when useful, "
                "avoid loops, explore unvisited squares, and seek the stairs or final boss."
            ),
        }
        started = time.perf_counter()
        configuration = self._settings.current()
        factory = self._client_factory or (
            lambda: TypeSafeClient(
                api_key=configuration.api_key,
                base_url=configuration.base_url,
            )
        )
        try:
            with factory() as client:
                response = client.system_one(
                    state=request_state,
                    questions={
                        "next_action": Choice(
                            instructions=(
                                "Which legal move best advances the long-term goal while managing "
                                "health, combat strength, keys, and repeated movement?"
                            ),
                            criteria=criteria,
                        )
                    },
                    model=configuration.model,
                )
        except Exception as exc:
            raise JevUnavailable(f"Jev request failed: {exc}") from exc
        elapsed = round((time.perf_counter() - started) * 1000)
        answers = getattr(response, "answers", None)
        if answers is None:
            answers = getattr(response, "choices", None)
        answer = answers["next_action"]
        return Decision(
            action_id=answer.choice,
            probabilities=dict(answer.probabilities),
            confidence=float(answer.confidence),
            model=getattr(response, "model", configuration.model),
            latency_ms=elapsed,
            mode="jev",
        )


class HeuristicDecisionEngine:
    """Offline baseline. Useful for UI smoke tests and side-by-side Jev evaluation."""

    def choose(self, state: GameState, candidates: list[ActionPreview]) -> Decision:
        started = time.perf_counter()
        raw_scores = {item.action_id: self._score(item) for item in candidates}
        best_id = max(raw_scores, key=raw_scores.get)  # type: ignore[arg-type]
        floor = min(raw_scores.values())
        weights = {key: value - floor + 1 for key, value in raw_scores.items()}
        total = sum(weights.values())
        probabilities = {key: round(value / total, 4) for key, value in weights.items()}
        peak = probabilities[best_id]
        count = len(probabilities)
        confidence = 1.0 if count == 1 else max(0.0, min(1.0, (count * peak - 1) / (count - 1)))
        return Decision(
            action_id=best_id,
            probabilities=probabilities,
            confidence=round(confidence, 3),
            model="deterministic-baseline-v1",
            latency_ms=round((time.perf_counter() - started) * 1000),
            mode="local",
        )

    @staticmethod
    def _score(item: ActionPreview) -> float:
        kind_bonus = {
            TileKind.STAIRS: 220,
            TileKind.BOSS: 260,
            TileKind.ATTACK_GEM: 110,
            TileKind.DEFENSE_GEM: 95,
            TileKind.BLUE_KEY: 75,
            TileKind.YELLOW_KEY: 60,
            TileKind.RED_POTION: 45,
            TileKind.BLUE_POTION: 65,
            TileKind.ENEMY: 18,
            TileKind.FLOOR: 5,
            TileKind.YELLOW_DOOR: -12,
            TileKind.BLUE_DOOR: -20,
        }.get(item.tile.kind, 0)
        return (
            kind_bonus
            + item.hp_delta * 0.08
            + item.attack_delta * 12
            + item.defense_delta * 10
            + item.gold_delta * 0.4
            - item.visit_count * 38
        )


class SafeJevDecisionEngine:
    """Keeps autoplay alive on API errors while exposing the fallback in telemetry."""

    def __init__(self, jev: JevDecisionEngine, fallback: HeuristicDecisionEngine) -> None:
        self._jev = jev
        self._fallback = fallback

    @property
    def configured(self) -> bool:
        return self._jev.configured

    def choose(self, state: GameState, candidates: list[ActionPreview]) -> Decision:
        try:
            return self._jev.choose(state, candidates)
        except JevUnavailable as exc:
            fallback = self._fallback.choose(state, candidates)
            return Decision(
                action_id=fallback.action_id,
                probabilities=fallback.probabilities,
                confidence=fallback.confidence,
                model=f"fallback: {exc}",
                latency_ms=fallback.latency_ms,
                mode="fallback",
            )
