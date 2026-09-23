from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from magic_tower.domain.models import ActionPreview, GameState


@dataclass(frozen=True, slots=True)
class Decision:
    action_id: str
    probabilities: dict[str, float]
    confidence: float
    model: str
    latency_ms: int
    mode: str


class DecisionEngine(Protocol):
    def choose(self, state: GameState, candidates: list[ActionPreview]) -> Decision: ...

