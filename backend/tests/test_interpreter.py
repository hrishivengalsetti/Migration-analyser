import os
import pytest
from unittest.mock import patch, MagicMock
from brain.interpreter import generate_narrative
from models import AIInterpretation, Evidence, ComparisonStatus

@pytest.fixture
def sample_inputs():
    return {
        "diff_summary": {"added": 1},
        "blast_radius_summary": {"directly_affected": 2},
        "execution_summary": {"passed": 5},
        "evidence_data": [
            Evidence(symbol_id="test", file="test.py", comparison=ComparisonStatus.REGRESSION, failing_tests=[], passing_tests=[], unverified_tests=[])
        ]
    }

@patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
@patch("brain.interpreter.Groq")
def test_successful_interpretation(mock_groq, sample_inputs):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content='{"migration_intent": "intent", "risk_summary": "risk", "key_concerns": ["c1"], "confidence": "high"}'))]
    mock_client.chat.completions.create.return_value = mock_response
    mock_groq.return_value = mock_client

    result = generate_narrative(**sample_inputs)
    
    assert result.migration_intent == "intent"
    assert result.confidence == "high"
    assert mock_client.chat.completions.create.call_count == 1

@patch.dict(os.environ, clear=True)
def test_missing_api_key_returns_fallback(sample_inputs):
    result = generate_narrative(**sample_inputs)
    assert result.confidence == "none"
    assert "unavailable" in result.migration_intent

@patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
@patch("brain.interpreter.Groq")
def test_api_timeout_returns_fallback(mock_groq, sample_inputs):
    from groq import APITimeoutError
    import httpx
    
    mock_client = MagicMock()
    request = httpx.Request("POST", "https://api.groq.com")
    mock_client.chat.completions.create.side_effect = APITimeoutError(request)
    mock_groq.return_value = mock_client

    result = generate_narrative(**sample_inputs)
    assert result.confidence == "none"

@patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
@patch("brain.interpreter.Groq")
def test_malformed_json_returns_fallback(mock_groq, sample_inputs):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content='{bad json}'))]
    mock_client.chat.completions.create.return_value = mock_response
    mock_groq.return_value = mock_client

    result = generate_narrative(**sample_inputs)
    assert result.confidence == "none"

@patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
@patch("brain.interpreter.Groq")
def test_prompt_contains_boundaries_and_evidence(mock_groq, sample_inputs):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content='{"migration_intent": "intent", "risk_summary": "risk", "key_concerns": [], "confidence": "high"}'))]
    mock_client.chat.completions.create.return_value = mock_response
    mock_groq.return_value = mock_client

    generate_narrative(**sample_inputs)
    
    call_args = mock_client.chat.completions.create.call_args[1]
    prompt_text = call_args["messages"][1]["content"]
    assert "[AUTHORITATIVE FACTS]" in prompt_text
    assert "[REQUIRED INTERPRETATION]" in prompt_text
