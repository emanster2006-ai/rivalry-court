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


def test_production_with_jwks_does_not_need_a_shared_secret() -> None:
    settings = make(
        app_env="production",
        auth_jwks_url="https://example.supabase.co/auth/v1/.well-known/jwks.json",
        database_url="postgresql+psycopg://rivalry:s3cure@db:5432/rivalry_court",
        web_url="https://rivalry.example.com",
    )
    assert settings.auth_jwks_url


def test_production_rejects_insecure_jwks_url() -> None:
    with pytest.raises(ValidationError, match="AUTH_JWKS_URL"):
        make(
            app_env="production",
            auth_jwks_url="http://example.com/jwks.json",
            database_url="postgresql+psycopg://rivalry:s3cure@db:5432/rivalry_court",
            web_url="https://rivalry.example.com",
        )
