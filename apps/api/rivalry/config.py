from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_JWT_SECRET = "replace-with-a-long-random-secret"


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://rivalry:change-me@localhost:5432/rivalry_court"
    auth_jwt_secret: str = DEFAULT_JWT_SECRET
    # Set to a JWKS URL (hosted Supabase) to verify public-key signed tokens instead of the shared secret.
    auth_jwks_url: str = ""
    web_url: str = "http://localhost:5173"
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    mail_from: str = "Rivalry Court <no-reply@rivalry.local>"
    app_env: str = "development"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def reject_unsafe_production_values(self) -> "Settings":
        if self.app_env != "production":
            return self
        problems = []
        weak_secret = len(self.auth_jwt_secret) < 32 or self.auth_jwt_secret == DEFAULT_JWT_SECRET
        if self.auth_jwks_url:
            if not self.auth_jwks_url.startswith("https://"):
                problems.append("AUTH_JWKS_URL must be https")
        elif weak_secret:
            problems.append("AUTH_JWT_SECRET must be a random value of 32+ characters")
        if "change-me" in self.database_url:
            problems.append("DATABASE_URL still contains the placeholder password")
        if not self.web_url.startswith("https://"):
            problems.append("WEB_URL must be https in production")
        if problems:
            raise ValueError("; ".join(problems))
        return self


settings = Settings()
