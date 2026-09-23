from magic_tower.application.game_service import GameService
from magic_tower.infrastructure.decision_engines import HeuristicDecisionEngine


def test_ai_step_returns_observable_decision() -> None:
    engine = HeuristicDecisionEngine()
    service = GameService(engine, engine)
    result = service.ai_step("local")
    assert result["turn"] == 1
    assert result["decision"]["mode"] == "local"
    assert result["decision"]["probabilities"]
    assert result["metrics"]["decisions"] == 1


def test_reset_clears_decision_metrics() -> None:
    engine = HeuristicDecisionEngine()
    service = GameService(engine, engine)
    service.ai_step("local")
    result = service.reset()
    assert result["turn"] == 0
    assert result["decision"] is None
    assert result["metrics"]["decisions"] == 0

