from core.auth.google_oauth import (
    create_oauth_state_token,
    generate_pkce_pair,
    parse_oauth_state_token,
    sanitize_return_to,
)


def test_generate_pkce_pair_produces_verifier_and_challenge():
    verifier, challenge = generate_pkce_pair()
    assert verifier
    assert challenge
    assert verifier != challenge


def test_oauth_state_token_roundtrip():
    verifier, _ = generate_pkce_pair()
    token = create_oauth_state_token(verifier, "/app/projects")
    payload = parse_oauth_state_token(token)
    assert payload.verifier == verifier
    assert payload.return_to == "/app/projects"


def test_sanitize_return_to_rejects_external_paths():
    assert sanitize_return_to("/app") == "/app"
    assert sanitize_return_to("//evil.com") == "/app"
    assert sanitize_return_to("https://evil.com/app") == "/app"
    assert sanitize_return_to(None) == "/app"
