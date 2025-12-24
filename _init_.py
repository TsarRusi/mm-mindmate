"""
MindMate Bot - психологический помощник в Telegram
Версия для Render.com
"""
__version__ = "1.0.0"
__author__ = "Your Name"

# Экспортируем основные модули
from . import bot
from . import database
from . import message_handlers
from . import nlp_analyzer
from . import deepseek_chat

__all__ = ['bot', 'database', 'message_handlers', 'nlp_analyzer', 'deepseek_chat']
