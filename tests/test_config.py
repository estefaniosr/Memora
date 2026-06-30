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
