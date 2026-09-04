import os
from pathlib import Path
from dotenv import load_dotenv

# Find the .env file (it's in the parent folder of config/)
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)


class Settings:
    """Reads all secrets from .env file."""

    # Gmail
    GMAIL_ADDRESS: str = os.getenv("GMAIL_ADDRESS", "")
    GMAIL_APP_PASSWORD: str = os.getenv("GMAIL_APP_PASSWORD", "")

    # PostgreSQL
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "email_automation")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    # AI (OpenRouter)
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "openrouter/free")

    # Polling
    POLL_INTERVAL_SECONDS: int = int(os.getenv("POLL_INTERVAL_SECONDS", "120"))

    @property
    def database_url(self) -> str:
        """Builds the PostgreSQL connection string."""
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    def validate(self) -> list:
        """Checks which required settings are missing."""
        missing = []
        if not self.GMAIL_ADDRESS:
            missing.append("GMAIL_ADDRESS")
        if not self.GMAIL_APP_PASSWORD:
            missing.append("GMAIL_APP_PASSWORD")
        if not self.OPENROUTER_API_KEY:
            missing.append("OPENROUTER_API_KEY")
        if not self.DB_PASSWORD:
            missing.append("DB_PASSWORD")
        return missing


# This is the single object every other file will import
settings = Settings()