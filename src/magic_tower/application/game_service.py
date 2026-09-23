from __future__ import annotations

from dataclasses import asdict
from threading import RLock
from typing import Any

from magic_tower.application.i18n import (
    action_description,
    event_text,
    floor_text,
    normalize_language,
    tile_text,
)
from magic_tower.application.ports import Decision, DecisionEngine
from magic_tower.domain.floors import FLOORS, tile_at
from magic_tower.domain.models import ActionPreview, Position, serialize_enemy
from magic_tower.domain.rules import IllegalMove, apply_action, legal_actions, new_game


class GameService:
    """Thread-safe use-case facade. HTTP and AI details do not leak into game rules."""

    def __init__(self, jev_engine: DecisionEngine, fallback_engine: DecisionEngine) -> None:
        self._lock = RLock()
        self._jev_engine = jev_engine
        self._fallback_engine = fallback_engine
        self._state = new_game()
        self._last_decision: Decision | None = None
        self._decision_history: list[Decision] = []

    def reset(self, language: str = "zh") -> dict[str, Any]:
        with self._lock:
            self._state = new_game()
            self._last_decision = None
            self._decision_history.clear()
            return self.snapshot(language)

    def move(self, action_id: str, language: str = "zh") -> dict[str, Any]:
        with self._lock:
            apply_action(self._state, action_id)
            self._last_decision = None
            return self.snapshot(language)

    def ai_step(self, mode: str = "jev", language: str = "zh") -> dict[str, Any]:
        with self._lock:
            candidates = legal_actions(self._state)
            if not candidates:
                self._state.lost = not self._state.won
                self._state.add_event("no_moves")
                return self.snapshot(language)
            engine = self._jev_engine if mode == "jev" else self._fallback_engine
            decision = engine.choose(self._state, candidates)
            if decision.action_id not in {candidate.action_id for candidate in candidates}:
                raise IllegalMove(f"Decision engine returned unknown action: {decision.action_id}")
            apply_action(self._state, decision.action_id)
            self._last_decision = decision
            self._decision_history.append(decision)
            del self._decision_history[:-30]
            return self.snapshot(language)

    def snapshot(self, language: str = "zh") -> dict[str, Any]:
        language = normalize_language(language)
        state = self._state
        floor = FLOORS[state.floor_index]
        localized_floor_name, localized_floor_subtitle = floor_text(state.floor_index, language)
        candidates = legal_actions(state)
        grid = []
        for row, line in enumerate(floor.layout):
            grid_row = []
            for col in range(len(line)):
                position = Position(row, col)
                tile = tile_at(state.floor_index, position, state.consumed)
                enemy = serialize_enemy(tile.enemy)
                if enemy:
                    enemy["name"] = tile_text(tile, language)
                grid_row.append(
                    {
                        "kind": tile.kind.value,
                        "label": tile_text(tile, language),
                        "icon": tile.icon,
                        "enemy": enemy,
                    }
                )
            grid.append(grid_row)
        return {
            "floor": {
                "index": state.floor_index,
                "number": state.floor_index + 1,
                "total": len(FLOORS),
                "name": localized_floor_name,
                "subtitle": localized_floor_subtitle,
                "palette": floor.palette,
            },
            "hero": asdict(state.hero),
            "position": asdict(state.position),
            "grid": grid,
            "turn": state.turn,
            "won": state.won,
            "lost": state.lost,
            "events": [event_text(item, language) for item in reversed(state.recent_events)],
            "actions": [self._serialize_action(item, language) for item in candidates],
            "decision": self._serialize_decision(self._last_decision),
            "metrics": self._metrics(),
        }

    @staticmethod
    def _serialize_action(action: ActionPreview, language: str) -> dict[str, Any]:
        return {
            "id": action.action_id,
            "direction": action.direction,
            "description": action_description(action, language),
            "destination": asdict(action.destination),
            "tile": tile_text(action.tile, language),
            "hp_delta": action.hp_delta,
            "attack_delta": action.attack_delta,
            "defense_delta": action.defense_delta,
            "gold_delta": action.gold_delta,
            "yellow_key_delta": action.yellow_key_delta,
            "blue_key_delta": action.blue_key_delta,
        }

    @staticmethod
    def _serialize_decision(decision: Decision | None) -> dict[str, Any] | None:
        return asdict(decision) if decision else None

    def _metrics(self) -> dict[str, Any]:
        if not self._decision_history:
            return {"decisions": 0, "average_confidence": 0, "average_latency_ms": 0}
        return {
            "decisions": len(self._decision_history),
            "average_confidence": round(
                sum(item.confidence for item in self._decision_history)
                / len(self._decision_history),
                3,
            ),
            "average_latency_ms": round(
                sum(item.latency_ms for item in self._decision_history)
                / len(self._decision_history)
            ),
        }
