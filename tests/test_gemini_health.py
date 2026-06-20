from __future__ import annotations

from unittest.mock import MagicMock, patch

from xtb_lab_harness.client.gemini_health import check_gemini, format_health_report


def test_check_gemini_missing_key(monkeypatch) -> None:
    monkeypatch.setattr("xtb_lab_harness.client.gemini_health.load_project_env", lambda: None)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    result = check_gemini()
    assert result.status == "missing_key"
    assert "GEMINI_API_KEY" in result.message


@patch("google.genai.Client")
def test_check_gemini_ok(mock_client_cls, monkeypatch) -> None:
    monkeypatch.setattr("xtb_lab_harness.client.gemini_health.load_project_env", lambda: None)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    mock_response = MagicMock()
    mock_response.text = "OK"
    mock_client_cls.return_value.models.generate_content.return_value = mock_response

    result = check_gemini(model="gemini-2.0-flash")
    assert result.status == "ok"
    assert result.response_preview == "OK"
    assert "정상" in format_health_report(result)
