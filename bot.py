#!/usr/bin/env python3
"""
MindMate Bot - психологический помощник
РАБОЧАЯ ВЕРСИЯ ДЛЯ RENDER - БЕЗ ОШИБОК ПРИ СТАРТЕ
"""

import os
import sys
import logging
from datetime import datetime

# Добавляем путь для импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# НАСТРОЙКА ЛОГГИРОВАНИЯ
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ============ ПРОВЕРКА ТОКЕНА ПЕРЕД ИМПОРТАМИ ============
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN не найден!")
    logger.error("Добавьте TELEGRAM_BOT_TOKEN в Environment Variables на Render")
    logger.info("Render Dashboard → Ваш сервис → Environment → Add Environment Variable")
    logger.info("Имя: TELEGRAM_BOT_TOKEN")
    logger.info("Значение: ваш_токен_от_BotFather")
    sys.exit(1)

logger.info(f"✅ Токен найден (первые 10 символов): {TOKEN[:10]}...")

# ============ ИМПОРТЫ С ЗАЩИТОЙ ОТ ОШИБОК ============

# 1. Сначала импортируем Telegram
try:
    from telegram import Update, ReplyKeyboardMarkup
    from telegram.ext import (
        Application, 
        CommandHandler, 
        MessageHandler, 
        filters,
        ContextTypes
    )
    logger.info("✅ Telegram библиотеки импортированы")
except ImportError as e:
    logger.error(f"❌ Не удалось импортировать telegram библиотеки: {e}")
    sys.exit(1)

# 2. Импортируем наши модули с защитой
try:
    # Сначала database - у него теперь есть заглушка
    from database import db_manager
    logger.info("✅ Модуль database импортирован")
except Exception as e:
    logger.error(f"❌ Критическая ошибка импорта database: {e}")
    sys.exit(1)

# 3. Импортируем обработчики
try:
    # Создаем простые заглушки обработчиков на случай ошибки
    async def start_stub(update, context):
        await update.message.reply_text("✅ MindMate Bot запущен! Используйте /help")
    
    async def help_stub(update, context):
        await update.message.reply_text("Помощь: /start, /help, /mood, /stats, /chat, /crisis")
    
    async def text_stub(update, context):
        await update.message.reply_text(f"Сообщение получено: {update.message.text[:50]}...")
    
    # Пробуем импортировать настоящие обработчики
    try:
        from message_handlers import (
            start,
            show_help,
            handle_text_message,
            start_chat,
            log_mood_command,
            show_stats,
            handle_crisis_situation,
            handle_unknown
        )
        logger.info("✅ Настоящие обработчики импортированы")
        USE_REAL_HANDLERS = True
    except ImportError as e:
        logger.warning(f"⚠️ Не удалось импортировать обработчики: {e}")
        logger.warning("⚠️ Используются заглушки обработчиков")
        start = start_stub
        show_help = help_stub
        handle_text_message = text_stub
        start_chat = start_stub
        log_mood_command = help_stub
        show_stats = help_stub
        handle_crisis_situation = help_stub
        handle_unknown = help_stub
        USE_REAL_HANDLERS = False
    
except Exception as e:
    logger.error(f"❌ Ошибка подготовки обработчиков: {e}")
    sys.exit(1)

# 4. Опциональные модули
try:
    from nlp_analyzer import nlp_analyzer
    NLP_AVAILABLE = True
    logger.info("✅ NLP анализатор импортирован")
except ImportError:
    NLP_AVAILABLE = False
    logger.warning("⚠️ NLP анализатор недоступен")

try:
    from deepseek_chat import deepseek_chat
    DEEPSEEK_AVAILABLE = True
    logger.info("✅ DeepSeek импортирован")
except ImportError:
    DEEPSEEK_AVAILABLE = False
    logger.warning("⚠️ DeepSeek недоступен")


# ============ КЛАСС БОТА ============

class MindMateBot:
    """Бот с защитой от всех ошибок"""
    
    def __init__(self):
        self.application = None
        logger.info("🧠 MindMate Bot инициализирован")
    
    async def init_database(self):
        """Инициализация базы данных (не ломает бота при ошибке)"""
        try:
            success = db_manager.init_db()
            if success:
                logger.info("✅ База данных инициализирована")
            else:
                logger.warning("⚠️ Проблема с инициализацией БД, но бот продолжит работу")
            return success
        except Exception as e:
            logger.warning(f"⚠️ Ошибка инициализации БД: {e}")
            logger.warning("⚠️ Бот будет работать без сохранения данных в БД")
            return False
    
    def setup_handlers(self):
        """Настройка обработчиков"""
        logger.info("🔄 Настройка обработчиков...")
        
        # Базовые команды
        self.application.add_handler(CommandHandler("start", start))
        self.application.add_handler(CommandHandler("help", show_help))
        self.application.add_handler(CommandHandler("crisis", handle_crisis_situation))
        self.application.add_handler(CommandHandler("stats", show_stats))
        self.application.add_handler(CommandHandler("mood", log_mood_command))
        self.application.add_handler(CommandHandler("chat", start_chat))
        self.application.add_handler(CommandHandler("ai", start_chat))
        
        # Текстовые сообщения
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text_message
        ))
        
        # Неизвестные команды
        self.application.add_handler(MessageHandler(
            filters.COMMAND,
            handle_unknown
        ))
        
        logger.info("✅ Обработчики настроены")
    
    def setup_error_handler(self):
        """Глобальный обработчик ошибок"""
        
        async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Обработчик ошибок, который не ломает бота"""
            try:
                error_msg = str(context.error) if context.error else "Неизвестная ошибка"
                logger.error(f"❌ Ошибка в боте: {error_msg}")
                
                # Отправляем пользователю сообщение
                if update and update.effective_message:
                    await update.effective_message.reply_text(
                        "⚠️ Произошла ошибка. Попробуйте еще раз или используйте /start",
                        parse_mode='Markdown'
                    )
            except Exception as e:
                logger.error(f"❌ Ошибка в обработчике ошибок: {e}")
        
        self.application.add_error_handler(error_handler)
        logger.info("✅ Обработчик ошибок настроен")
    
    async def on_startup(self, application):
        """Действия при запуске бота"""
        logger.info("=" * 60)
        logger.info("🚀 MindMate Bot ЗАПУЩЕН!")
        logger.info("=" * 60)
        
        # Информация о системе
        logger.info(f"🐍 Python: {sys.version}")
        logger.info(f"📁 Директория: {os.getcwd()}")
        logger.info(f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Проверка модулей
        logger.info(f"📊 База данных: {'✅ Доступна' if hasattr(db_manager, 'init_db') else '⚠️ Заглушка'}")
        logger.info(f"🧠 NLP анализ: {'✅ Доступен' if NLP_AVAILABLE else '⚠️ Недоступен'}")
        logger.info(f"🤖 DeepSeek AI: {'✅ Доступен' if DEEPSEEK_AVAILABLE else '⚠️ Недоступен'}")
        logger.info(f"🎮 Обработчики: {'✅ Настоящие' if USE_REAL_HANDLERS else '⚠️ Заглушки'}")
        
        # Инициализация БД
        await self.init_database()
        
        logger.info("✅ Бот готов к приему сообщений")
        logger.info("=" * 60)
    
    async def on_shutdown(self, application):
        """Действия при остановке бота"""
        logger.info("=" * 60)
        logger.info("🛑 MindMate Bot останавливается...")
        logger.info("=" * 60)
    
    def run(self):
        """Запуск бота"""
        try:
            # Проверяем среду
            is_render = os.environ.get('RENDER') is not None
            environment = "🌐 Render.com" if is_render else "💻 Локальная разработка"
            logger.info(f"Среда выполнения: {environment}")
            
            # Создаем приложение
            logger.info("🛠️ Создание Application...")
            self.application = Application.builder().token(TOKEN).build()
            
            # Настраиваем обработчики
            self.setup_handlers()
            self.setup_error_handler()
            
            # Добавляем обработчики запуска/остановки
            self.application.post_init = self.on_startup
            self.application.post_shutdown = self.on_shutdown
            
            # Запускаем бота
            logger.info("=" * 60)
            logger.info("🎯 БОТ ЗАПУЩЕН И ГОТОВ К РАБОТЕ!")
            logger.info("=" * 60)
            
            # Параметры polling для Render
            self.application.run_polling(
                drop_pending_updates=True,
                timeout=30,
                read_timeout=30,
                connect_timeout=30,
                pool_timeout=30,
                close_loop=False  # Важно для Render!
            )
            
        except KeyboardInterrupt:
            logger.info("🛑 Остановка по запросу пользователя (Ctrl+C)")
        except Exception as e:
            logger.error("=" * 60)
            logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА ПРИ ЗАПУСКЕ: {e}")
            logger.error("=" * 60)
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            sys.exit(1)


# ============ ЗАПУСК ============

def main():
    """Точка входа"""
    logger.info("=" * 60)
    logger.info("🧠 ЗАПУСК MINDMATE BOT")
    logger.info("=" * 60)
    
    # Проверка версии Python
    if sys.version_info < (3, 9):
        logger.error(f"❌ Требуется Python 3.9+, текущая версия: {sys.version}")
        return
    
    # Запуск
    bot = MindMateBot()
    bot.run()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 Приложение остановлено пользователем")
    except Exception as e:
        logger.error(f"❌ Необработанная ошибка: {e}")
