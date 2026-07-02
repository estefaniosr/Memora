import pytest

from app.config import ConfigurationError, load_settings


def test_invalid_llm_provider_has_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "provider-inexistente")

    with pytest.raises(ConfigurationError, match="LLM_PROVIDER inválido"):
        load_settings()


def test_openai_credentials_are_required_only_when_selected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("OPENAI_MODEL", "")

    with pytest.raises(ConfigurationError, match="OPENAI_API_KEY, OPENAI_MODEL"):
        load_settings()


def test_local_settings_do_not_require_confluence(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    for name in (
        "CONFLUENCE_BASE_URL",
        "CONFLUENCE_EMAIL",
        "CONFLUENCE_API_TOKEN",
        "CONFLUENCE_SPACE_KEY",
    ):
        monkeypatch.setenv(name, "")

    settings = load_settings()

    assert settings.confluence_base_url == ""


def test_confluence_can_be_required_explicitly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONFLUENCE_BASE_URL", "")

    with pytest.raises(ConfigurationError, match="CONFLUENCE_BASE_URL"):
        load_settings(require_confluence=True)
