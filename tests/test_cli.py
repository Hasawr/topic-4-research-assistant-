import argparse
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock


def test_validate_question_accepts_clean_question():
    from src.cli import validate_question

    result = validate_question("  What is quantum computing?  ")

    assert result == "What is quantum computing?"


def test_empty_question_rejected():
    from src.cli import validate_question

    with pytest.raises(SystemExit) as exc:
        validate_question("   ")

    assert exc.value.code == 1


def test_oversized_question_rejected():
    from src.cli import validate_question, MAX_QUESTION_LENGTH

    huge_question = "x" * (MAX_QUESTION_LENGTH + 1)

    with pytest.raises(SystemExit) as exc:
        validate_question(huge_question)

    assert exc.value.code == 1


def test_validate_sources_returns_none_when_missing():
    from src.cli import validate_sources

    assert validate_sources(None) is None


def test_sources_flag_filters_correctly():
    from src.cli import validate_sources

    result = validate_sources("wiki, arxiv, web")

    assert result == ["wiki", "arxiv", "web"]


def test_sources_are_lowercased_and_trimmed():
    from src.cli import validate_sources

    result = validate_sources(" WIKI , ArXiV , Tavily ")

    assert result == ["wiki", "arxiv", "tavily"]


def test_invalid_source_rejected():
    from src.cli import validate_sources

    with pytest.raises(SystemExit) as exc:
        validate_sources("wiki,google")

    assert exc.value.code == 1


def test_display_citations_with_dicts(capsys):
    from src.cli import display_citations

    citations = [
        {
            "index": 1,
            "source": {
                "title": "Quantum Computing Article",
                "url": "https://example.com/quantum",
                "origin": "wiki",
            },
        }
    ]

    display_citations(citations)

    captured = capsys.readouterr()

    assert "SOURCES & CITATIONS" in captured.out
    assert "[1] (WIKI) Quantum Computing Article" in captured.out
    assert "URL: https://example.com/quantum" in captured.out


def test_display_citations_with_objects(capsys):
    from src.cli import display_citations

    source = SimpleNamespace(
        title="Arxiv Paper",
        url="https://arxiv.org/example",
        origin="arxiv",
    )

    citation = SimpleNamespace(index=2, source=source)

    display_citations([citation])

    captured = capsys.readouterr()

    assert "[2] (ARXIV) Arxiv Paper" in captured.out
    assert "URL: https://arxiv.org/example" in captured.out


def test_display_citations_empty_outputs_nothing(capsys):
    from src.cli import display_citations

    display_citations([])

    captured = capsys.readouterr()

    assert captured.out == ""


def test_handle_ask_success_dict_result(monkeypatch, capsys):
    import src.cli as cli

    mock_assistant = Mock()
    mock_assistant.conduct_research = AsyncMock(
        return_value={
            "answer": "This is a fake research answer.",
            "citations": [
                {
                    "index": 1,
                    "source": {
                        "title": "Fake Source",
                        "url": "https://example.com",
                        "origin": "web",
                    },
                }
            ],
        }
    )

    mock_research_assistant_class = Mock(return_value=mock_assistant)
    monkeypatch.setattr(cli, "ResearchAssistant", mock_research_assistant_class)

    args = argparse.Namespace(
        question="What is AI?",
        no_cache=True,
        sources="wiki,arxiv",
    )

    cli.handle_ask(args)

    captured = capsys.readouterr()

    assert "AI RESEARCH ASSISTANT REPORT" in captured.out
    assert "QUESTION: What is AI?" in captured.out
    assert "This is a fake research answer." in captured.out
    assert "[1] (WEB) Fake Source" in captured.out

    mock_assistant.conduct_research.assert_awaited_once_with(
        query="What is AI?",
        no_cache=True,
        sources=["wiki", "arxiv"],
    )


def test_handle_ask_success_object_result(monkeypatch, capsys):
    import src.cli as cli

    result = SimpleNamespace(
        answer="Object-style answer.",
        citations=[
            SimpleNamespace(
                index=1,
                source=SimpleNamespace(
                    title="Object Source",
                    url="https://example.com/object",
                    origin="wiki",
                ),
            )
        ],
    )

    mock_assistant = Mock()
    mock_assistant.conduct_research = AsyncMock(return_value=result)

    monkeypatch.setattr(cli, "ResearchAssistant", Mock(return_value=mock_assistant))

    args = argparse.Namespace(
        question="What is Python?",
        no_cache=False,
        sources=None,
    )

    cli.handle_ask(args)

    captured = capsys.readouterr()

    assert "Object-style answer." in captured.out
    assert "[1] (WIKI) Object Source" in captured.out

    mock_assistant.conduct_research.assert_awaited_once_with(
        query="What is Python?",
        no_cache=False,
        sources=None,
    )


def test_handle_ask_exits_on_engine_error(monkeypatch):
    import src.cli as cli

    mock_assistant = Mock()
    mock_assistant.conduct_research = AsyncMock(side_effect=RuntimeError("engine failed"))

    monkeypatch.setattr(cli, "ResearchAssistant", Mock(return_value=mock_assistant))

    args = argparse.Namespace(
        question="What is AI?",
        no_cache=False,
        sources=None,
    )

    with pytest.raises(SystemExit) as exc:
        cli.handle_ask(args)

    assert exc.value.code == 1