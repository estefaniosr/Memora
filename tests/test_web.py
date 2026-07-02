from app.web import _is_generation_model


def test_openai_exposes_only_generation_models() -> None:
    assert _is_generation_model("openai", "gpt-4.1-mini")
    assert _is_generation_model("openai", "o3-mini")
    assert not _is_generation_model("openai", "text-embedding-3-small")
    assert not _is_generation_model("openai", "whisper-1")


def test_gemini_exposes_only_gemini_models() -> None:
    assert _is_generation_model("gemini", "models/gemini-2.5-flash")
    assert not _is_generation_model("gemini", "models/imagen-3.0-generate-002")
    assert not _is_generation_model("gemini", "models/text-embedding-004")


def test_ollama_hides_embedding_models() -> None:
    assert _is_generation_model("ollama", "llama3.1:8b", "llama")
    assert not _is_generation_model("ollama", "nomic-embed-text", "nomic-bert")
    assert not _is_generation_model("ollama", "custom-model", "bert")
