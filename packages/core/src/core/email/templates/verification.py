from dataclasses import dataclass


@dataclass(frozen=True)
class VerificationEmailContent:
    subject: str
    text_body: str
    html_body: str


def render_verification_email(code: str, expires_minutes: int) -> VerificationEmailContent:
    subject = "Your DashZen verification code"
    text_body = f"""Hi,

Your verification code is: {code}

This code expires in {expires_minutes} minutes.

If you didn't create a DashZen account, you can ignore this email.

— DashZen Team
"""
    html_body = f"""<!DOCTYPE html>
<html>
<body style="font-family: sans-serif; line-height: 1.5; color: #111;">
  <p>Hi,</p>
  <p>Your verification code is:</p>
  <p style="font-size: 28px; font-weight: bold; letter-spacing: 4px; font-family: monospace;">
    {code}
  </p>
  <p>This code expires in <strong>{expires_minutes} minutes</strong>.</p>
  <p style="color: #666; font-size: 14px;">
    If you didn't create a DashZen account, you can ignore this email.
  </p>
  <p>— DashZen Team</p>
</body>
</html>
"""
    return VerificationEmailContent(subject=subject, text_body=text_body, html_body=html_body)
