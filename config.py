import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Настройки приложения для Render"""
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # DeepSeek API
    DEEPSEEK_API_KEY: Optional[str] = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_API_URL: str = "https://api.deepseek.com/v1/chat/completions"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///mindmate.db")
    
    # App Settings
    APP_NAME: str = "MindMate Bot"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # NLP Settings
    NLP_MODEL: str = "simple"  # Используем простую NLP модель для Render
    
    # Security
    ALLOWED_USERS: list = []  # Пустой список = разрешены все
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Создаем глобальный экземпляр настроек
settings = Settings()
