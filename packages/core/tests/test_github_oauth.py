from core.auth.github_oauth import pick_primary_verified_email


def test_pick_primary_verified_email_prefers_primary():
    emails = [
        {"email": "other@example.com", "primary": False, "verified": True},
        {"email": "Primary@Example.com", "primary": True, "verified": True},
    ]
    assert pick_primary_verified_email(emails) == "primary@example.com"


def test_pick_primary_verified_email_falls_back_to_any_verified():
    emails = [
        {"email": "a@example.com", "primary": False, "verified": False},
        {"email": "b@example.com", "primary": False, "verified": True},
    ]
    assert pick_primary_verified_email(emails) == "b@example.com"


def test_pick_primary_verified_email_returns_none_when_unverified():
    emails = [{"email": "a@example.com", "primary": True, "verified": False}]
    assert pick_primary_verified_email(emails) is None


def test_pick_primary_verified_email_accepts_noreply():
    emails = [
        {
            "email": "123456+noreply@users.noreply.github.com",
            "primary": True,
            "verified": True,
        },
    ]
    assert pick_primary_verified_email(emails) == "123456+noreply@users.noreply.github.com"
