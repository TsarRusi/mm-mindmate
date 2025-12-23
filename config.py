import os
import logging
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class Settings(BaseSettings):
    """Настройки приложения."""
    
    # Основные
    TELEGRAM_BOT_TOKEN: str
    ADMIN_IDS: List[int] = []
    
    # База данных
    DATABASE_URL: str = "sqlite:///mindmate.db"
    
    # DeepSeek API
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_API_URL: str = "https://api.deepseek.com/v1/chat/completions"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    
    # Настройки бота
    LOG_LEVEL: str = "INFO"
    TIMEZONE: str = "Europe/Moscow"
    LANGUAGE: str = "ru"
    
    # Напоминания
    ENABLE_REMINDERS: bool = True
    DAILY_CHECKIN_TIME: str = "19:00"
    WEEKLY_REPORT_DAY: int = 1  # Вторник
    
    # Лимиты
    MAX_MESSAGES_PER_DAY: int = 50
    MAX_SESSION_DURATION: int = 30  # минут
    
    # Пути
    BASE_DIR: Path = Path(__file__).parent
    LOGS_DIR: Path = BASE_DIR / "logs"
    
    class Config:
        env_file = ".env"
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Преобразуем ADMIN_IDS из строки в список int
        if isinstance(self.ADMIN_IDS, str):
            self.ADMIN_IDS = [int(x.strip()) for x in self.ADMIN_IDS.split(',') if x.strip()]
    
    def setup_logging(self):
        """Настройка логирования."""
        self.LOGS_DIR.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, self.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.LOGS_DIR / "bot.log"),
                logging.StreamHandler()
            ]
        )

# Создаем экземпляр настроек
settings = Settings()
settings.setup_logging()

# Кризисные контакты (Россия)
CRISIS_CONTACTS = {
    'telephone': [
        '📞 **Телефон доверия:** 8-800-2000-122 (бесплатно, круглосуточно)',
        '📞 **Московская служба психологической помощи:** +7 (495) 051 (круглосуточно)',
        '📞 **Кризисный чат:** https://pruffme.com/landing/psi911'
    ],
    'online': [
        '🌐 **Ясное утро:** https://yasnoe-utro.ru (чат с психологом)',
        '🌐 **Твоя территория:** https://www.xn--b1agja1acmacmce7nj.xn--80asehdb (помощь подросткам)',
        '🌐 **Помощь рядом:** https://helpnear.ru (карта бесплатных центров)'
    ],
    'emergency': [
        '🚨 **Скорая помощь:** 103',
        '🚨 **МЧС:** 112',
        '🚨 **Полиция:** 102'
    ]
}