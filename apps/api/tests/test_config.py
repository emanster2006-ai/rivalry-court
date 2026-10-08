import pytest
from pydantic import ValidationError

from rivalry.config import Settings


def make(**overrides) -> Settings:
    defaults = {
        "database_url": "postgresql+psycopg://rivalry:change-me@localhost:5432/rivalry_court",
        "auth_jwt_secret": "replace-with-a-long-random-secret",
        "web_url": "http://localhost:5173",
    }
    return Settings(_env_file=None, **(defaults | overrides))


def test_development_allows_placeholder_values() -> None:
    assert make(app_env="development").auth_jwt_secret


def test_production_rejects_placeholders() -> None:
    with pytest.raises(ValidationError) as error:
        make(app_env="production")
    message = str(error.value)
    assert "AUTH_JWT_SECRET" in message
    assert "placeholder password" in message
    assert "https" in message


def test_production_accepts_real_values() -> None:
    settings = make(
        app_env="production",
        auth_jwt_secret="x" * 40,
        database_url="postgresql+psycopg://rivalry:s3cure@db:5432/rivalry_court",
        web_url="https://rivalry.example.com",
    )
    assert settings.app_env == "production"
