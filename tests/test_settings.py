import pytest

from magic_tower.application.settings import JevSettings


def test_environment_is_the_default_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TYPESAFE_API_KEY", "env-secret-key")
    monkeypatch.setenv("TYPESAFE_MODEL", "jev-env")
    settings = JevSettings()
    snapshot = settings.public_snapshot()
    assert snapshot["source"] == "environment"
    assert snapshot["configured"] is True
    assert snapshot["model"] == "jev-env"
    assert "env-secret-key" not in str(snapshot)


def test_page_configuration_is_in_memory_and_can_reset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TYPESAFE_API_KEY", "env-key-1234")
    settings = JevSettings()
    configured = settings.configure(
        api_key="page-key-5678",
        base_url="http://localhost:8088/",
        model="openjev-test",
    )
    assert configured["source"] == "page"
    assert settings.current().api_key == "page-key-5678"
    assert settings.current().base_url == "http://localhost:8088"

    reset = settings.reset_to_environment()
    assert reset["source"] == "environment"
    assert settings.current().api_key == "env-key-1234"


def test_page_configuration_rejects_invalid_api_url() -> None:
    settings = JevSettings()
    with pytest.raises(ValueError, match="API 地址"):
        settings.configure(api_key="key", base_url="not-a-url", model="jev-latest")

