import json
from types import SimpleNamespace

from backend.app.ai import analyze_with_ai
from backend.app.config import Settings


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeClient:
    def __init__(self, payload):
        self.payload = payload
        self.request = None

    def post(self, url, *, headers, json):
        self.request = {"url": url, "headers": headers, "json": json}
        return FakeResponse(self.payload)


def configured_settings():
    return Settings(
        database_url="sqlite://",
        openai_api_key="test-key",
        openai_model="gpt-4o-mini",
        ai_timeout_seconds=1,
    )


def sample_rule():
    return SimpleNamespace(
        rule_key="TONE-001",
        rule_type="tone",
        title="Warm and calm",
        content="Use warm, calm language.",
        replacement=None,
    )


def test_no_key_returns_truthful_unavailable_state_without_calling_provider():
    result = analyze_with_ai(
        "Safe copy",
        [],
        config=Settings("sqlite://", None, "gpt-4o-mini", 1),
    )

    assert result.status == "unavailable"
    assert result.findings == []
    assert "not configured" in result.error.lower()


def test_malformed_structured_output_is_not_displayed_as_a_finding():
    client = FakeClient({"output_text": json.dumps({"not_findings": []})})

    result = analyze_with_ai("Safe copy", [sample_rule()], config=configured_settings(), client=client)

    assert result.status == "failed"
    assert result.findings == []
    assert "invalid result" in result.error.lower()


def test_unknown_rule_reference_is_rejected_even_when_provider_output_is_valid_json():
    client = FakeClient(
        {
            "output_text": json.dumps(
                {
                    "findings": [
                        {
                            "severity": "medium",
                            "category": "tone",
                            "label": "tone mismatch",
                            "explanation": "The wording is too abrupt.",
                            "suggestion": "Use a warmer phrase.",
                            "excerpt": "Buy now.",
                            "rule_keys": ["INVENTED-999"],
                        }
                    ]
                }
            )
        }
    )

    result = analyze_with_ai("Buy now.", [sample_rule()], config=configured_settings(), client=client)

    assert result.status == "completed"
    assert result.findings == []
    assert client.request["json"]["text"]["format"]["strict"] is True
