from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://rivalry:change-me@localhost:5432/rivalry_court"
    auth_jwt_secret: str = "replace-with-a-long-random-secret"
    web_url: str = "http://localhost:5173"
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    mail_from: str = "Rivalry Court <no-reply@rivalry.local>"
    app_env: str = "development"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
