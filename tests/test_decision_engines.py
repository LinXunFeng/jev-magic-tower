from types import SimpleNamespace

from typing_extensions import Self

from magic_tower.domain.models import ActionPreview, Hero, Position, Tile, TileKind
from magic_tower.domain.rules import new_game
from magic_tower.infrastructure.decision_engines import (
    HeuristicDecisionEngine,
    JevDecisionEngine,
    SafeJevDecisionEngine,
)


def candidate(action_id: str, kind: TileKind, visits: int = 0) -> ActionPreview:
    return ActionPreview(
        action_id=action_id,
        direction=action_id.removeprefix("move_"),
        destination=Position(1, 1),
        tile=Tile(kind, kind.value, ""),
        visit_count=visits,
    )


def test_baseline_prefers_stairs_over_revisited_floor() -> None:
    decision = HeuristicDecisionEngine().choose(
        new_game(),
        [candidate("move_left", TileKind.FLOOR, visits=2), candidate("move_up", TileKind.STAIRS)],
    )
    assert decision.action_id == "move_up"
    assert abs(sum(decision.probabilities.values()) - 1) < 0.001
    assert 0 <= decision.confidence <= 1


def test_baseline_prefers_permanent_growth() -> None:
    state = new_game()
    state.hero = Hero()
    decision = HeuristicDecisionEngine().choose(
        state,
        [candidate("move_left", TileKind.FLOOR), candidate("move_right", TileKind.ATTACK_GEM)],
    )
    assert decision.action_id == "move_right"


class FakeClient:
    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def system_one(self, **_kwargs: object) -> SimpleNamespace:
        answer = SimpleNamespace(
            choice="move_up",
            probabilities={"move_up": 0.8, "move_left": 0.2},
            confidence=0.75,
        )
        return SimpleNamespace(model="jev-test", answers={"next_action": answer})


def test_jev_adapter_reads_current_sdk_response_shape() -> None:
    decision = JevDecisionEngine(client_factory=FakeClient).choose(
        new_game(),
        [candidate("move_up", TileKind.STAIRS), candidate("move_left", TileKind.FLOOR)],
    )
    assert decision.action_id == "move_up"
    assert decision.model == "jev-test"
    assert decision.probabilities["move_up"] == 0.8


def test_safe_jev_engine_marks_fallback_when_unconfigured(monkeypatch) -> None:
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    baseline = HeuristicDecisionEngine()
    safe_engine = SafeJevDecisionEngine(JevDecisionEngine(), baseline)
    decision = safe_engine.choose(new_game(), [candidate("move_up", TileKind.STAIRS)])
    assert decision.mode == "fallback"
    assert decision.model.startswith("fallback:")
