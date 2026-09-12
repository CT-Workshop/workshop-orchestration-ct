from app.services.partner_webhook_service import sanitize_request_headers


def test_sanitize_request_headers_redacts_credentials() -> None:
    raw = {
        "content-type": "application/json",
        "Authorization": "Bearer test-token",
        "Cookie": "session=abc",
        "X-Api-Key": "demo-key",
        "x-request-id": "req-1",
    }
    out = sanitize_request_headers(raw)
    assert out is not None
    assert out["content-type"] == "application/json"
    assert out["x-request-id"] == "req-1"
    assert out["Authorization"] == "[REDACTED]"
    assert out["Cookie"] == "[REDACTED]"
    assert out["X-Api-Key"] == "[REDACTED]"


def test_sanitize_request_headers_none() -> None:
    assert sanitize_request_headers(None) is None
