#!/usr/bin/env python3
"""Configuration management for Rosary Bot"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration settings"""

    # API Keys
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # RSS Settings
    RSS_URL = "https://feeds.fireside.fm/rosaryinayear/rss"
    SKIP_INTRO_EPISODE = True  # Skip episode 0 (intro)

    # File Settings
    DOWNLOAD_DIR = "downloads"
    SAVE_TRANSCRIPTS = True
    SAVE_SUMMARIES = True  # Save GPT summaries to text files
    CLEANUP_FILES = True  # Delete files after successful Telegram delivery

    # OpenAI Settings
    OPENAI_MODELS = ["gpt-4o-mini"]  # Using only GPT-4o Mini for cost efficiency

    # Whisper Settings
    WHISPER_MODEL = "base"  # tiny, base, small, medium, large

    # Selenium Settings
    SELENIUM_WAIT_TIME = 20
    CHATGPT_URL = "https://chat.openai.com"

    @classmethod
    def validate(cls):
        """Validate required environment variables"""
        missing = []

        if not cls.TELEGRAM_BOT_TOKEN:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not cls.TELEGRAM_USER_ID:
            missing.append("TELEGRAM_USER_ID")
        if not cls.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")

        if missing:
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")

        return True


# Initialize and validate configuration
try:
    Config.validate()
except ValueError as e:
    print(f"Configuration Error: {e}")
    print("Please check your .env file contains all required variables.")
    exit(1)
