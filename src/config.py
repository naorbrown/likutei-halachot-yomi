"""
Configuration management for Likutei Halachot Yomi bot.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class Config:
    """Application configuration."""

    # Telegram settings
    telegram_bot_token: str
    telegram_chat_id: str

    # Sefaria API
    sefaria_api_base: str = "https://www.sefaria.org/api"
    sefaria_timeout: int = 30

    # Paths
    base_dir: Path = Path(__file__).parent.parent
    data_dir: Path = None
    logs_dir: Path = None

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    # Message settings
    max_message_length: int = 4000
    include_sefaria_links: bool = True

    def __post_init__(self):
        if self.data_dir is None:
            self.data_dir = self.base_dir / "data"
        if self.logs_dir is None:
            self.logs_dir = self.base_dir / "logs"

        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables."""
        token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        if not chat_id:
            raise ValueError("TELEGRAM_CHAT_ID environment variable is required")

        return cls(
            telegram_bot_token=token,
            telegram_chat_id=chat_id,
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )

    @classmethod
    def for_testing(cls) -> "Config":
        """Create config for testing (no actual Telegram sending)."""
        return cls(
            telegram_bot_token="test_token",
            telegram_chat_id="test_chat_id",
        )


def get_config() -> Config:
    """Get application configuration."""
    try:
        return Config.from_env()
    except ValueError:
        # Return test config if env vars not set
        return Config.for_testing()
