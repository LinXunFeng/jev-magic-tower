from magic_tower.application.game_service import GameService
from magic_tower.application.i18n import normalize_language
from magic_tower.infrastructure.decision_engines import HeuristicDecisionEngine


def test_language_normalization_supports_browser_locale_codes() -> None:
    assert normalize_language("zh-CN") == "zh"
    assert normalize_language("en-US") == "en"
    assert normalize_language("fr-FR") == "en"


def test_english_snapshot_localizes_game_content() -> None:
    engine = HeuristicDecisionEngine()
    service = GameService(engine, engine)
    snapshot = service.snapshot("en-US")
    assert snapshot["floor"]["name"] == "Forgotten Gallery"
    assert snapshot["events"][0] == "The hero enters the Forgotten Tower."
    assert all("This square has been visited" in action["description"] for action in snapshot["actions"])
    assert snapshot["grid"][1][3]["enemy"]["name"] == "Green Slime"


def test_chinese_snapshot_remains_the_default() -> None:
    engine = HeuristicDecisionEngine()
    service = GameService(engine, engine)
    snapshot = service.snapshot()
    assert snapshot["floor"]["name"] == "遗忘回廊"
    assert snapshot["events"][0] == "勇者踏入遗忘之塔。"
