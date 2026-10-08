from typing import ClassVar

from rivalry import mail
from rivalry.config import settings


class FakeSMTP:
    instances: ClassVar[list["FakeSMTP"]] = []

    def __init__(self, host, port, timeout=None) -> None:
        self.calls: list[str] = [f"connect {host}:{port}"]
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *_exc) -> None:
        return None

    def starttls(self) -> None:
        self.calls.append("starttls")

    def login(self, user, _password) -> None:
        self.calls.append(f"login {user}")

    def send_message(self, msg) -> None:
        self.calls.append(f"send {msg['To']}")


def test_notice_encrypts_before_logging_in_when_starttls_is_enabled(monkeypatch) -> None:
    FakeSMTP.instances.clear()
    monkeypatch.setattr(mail.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(settings, "smtp_starttls", True)
    monkeypatch.setattr(settings, "smtp_user", "user@smtp-brevo.com")
    mail.send_score_notice(["a@example.com"], "duel-1")
    assert FakeSMTP.instances[0].calls == [
        f"connect {settings.smtp_host}:{settings.smtp_port}",
        "starttls",
        "login user@smtp-brevo.com",
        "send a@example.com",
    ]


def test_local_mailpit_mode_skips_starttls_and_login(monkeypatch) -> None:
    FakeSMTP.instances.clear()
    monkeypatch.setattr(mail.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(settings, "smtp_starttls", False)
    monkeypatch.setattr(settings, "smtp_user", "")
    mail.send_score_notice(["a@example.com"], "duel-1")
    assert "starttls" not in FakeSMTP.instances[0].calls
    assert not any(call.startswith("login") for call in FakeSMTP.instances[0].calls)
