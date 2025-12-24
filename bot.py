#!/usr/bin/env python3
"""
MindMate Bot - психологический помощник
ФИНАЛЬНАЯ РАБОЧАЯ ВЕРСИЯ ДЛЯ RENDER
"""

import os
import sys
import logging
from datetime import datetime

# Добавляем путь для импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# НАСТРОЙКА ЛОГГИРОВАНИЯ - ВАЖНО ДЛЯ RENDER!
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ИМПОРТЫ TELEGRAM
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters,
    ContextTypes
)

# ИМПОРТЫ НАШЕГО ПРИЛОЖЕНИЯ (С ЗАЩИТОЙ ОТ ОШИБОК)
try:
    # Импортируем функции НАПРЯМУЮ
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
    logger.info("✅ Все обработчики импортированы")
except ImportError as e:
    logger.error(f"❌ Ошибка импорта обработчиков: {e}")
    # Создаем заглушки
    async def start(update, context): await update.message.reply_text("Бот запущен!")
    async def show_help(update, context): await update.message.reply_text("Помощь")
    async def handle_text_message(update, context): await update.message.reply_text("Сообщение получено")
    async def start_chat(update, context): await update.message.reply_text("Чат с ИИ")
    async def log_mood_command(update, context): await update.message.reply_text("Оцените настроение")
    async def show_stats(update, context): await update.message.reply_text("Статистика")
    async def handle_crisis_situation(update, context): await update.message.reply_text("Экстренная помощь")
    async def handle_unknown(update, context): await update.message.reply_text("Неизвестная команда")
    logger.warning("⚠️ Используются заглушки обработчиков")

# ИМПОРТ БАЗЫ ДАННЫХ С ЗАЩИТОЙ
try:
    from database import db_manager
    logger.info("✅ База данных импортирована")
    DB_AVAILABLE = True
except ImportError as e:
    logger.error(f"❌ База данных недоступна: {e}")
    # Создаем заглушку БД
    class FakeDB:
        def init_db(self): return True
        def add_user(self, *args, **kwargs): return {"id": 1, "telegram_id": args[0]}
        def add_mood_log(self, *args, **kwargs): return {"id": 1}
    db_manager = FakeDB()
    DB_AVAILABLE = False
    logger.warning("⚠️ Используется заглушка базы данных")

# ИМПОРТ NLP АНАЛИЗАТОРА
try:
    from nlp_analyzer import nlp_analyzer
    logger.info("✅ NLP анализатор импортирован")
    NLP_AVAILABLE = True
except ImportError as e:
    logger.error(f"❌ NLP анализатор недоступен: {e}")
    nlp_analyzer = None
    NLP_AVAILABLE = False

# ИМПОРТ DEEPSEEK
try:
    from deepseek_chat import deepseek_chat
    logger.info("✅ DeepSeek импортирован")
    DEEPSEEK_AVAILABLE = True
except ImportError as e:
    logger.error(f"❌ DeepSeek недоступен: {e}")
    deepseek_chat = None
    DEEPSEEK_AVAILABLE = False


class MindMateBot:
    """ГЛАВНЫЙ КЛАСС БОТА С ИСПРАВЛЕНИЕМ ВСЕХ ОШИБОК"""
    
    def __init__(self):
        self.application = None
        logger.info("🧠 MindMate Bot инициализирован")
    
    def setup_handlers(self):
        """НАСТРОЙКА ВСЕХ ОБРАБОТЧИКОВ (БЕЗ ОШИБОК!)"""
        logger.info("🔄 Настройка обработчиков...")
        
        # КОМАНДА /start
        self.application.add_handler(CommandHandler("start", self.safe_start))
        logger.info("  ✅ Команда /start добавлена")
        
        # КОМАНДА /help
        self.application.add_handler(CommandHandler("help", self.safe_show_help))
        logger.info("  ✅ Команда /help добавлена")
        
        # КОМАНДА /crisis
        self.application.add_handler(CommandHandler("crisis", self.safe_handle_crisis))
        logger.info("  ✅ Команда /crisis добавлена")
        
        # КОМАНДА /stats
        self.application.add_handler(CommandHandler("stats", self.safe_show_stats))
        logger.info("  ✅ Команда /stats добавлена")
        
        # КОМАНДА /mood
        self.application.add_handler(CommandHandler("mood", self.safe_log_mood))
        logger.info("  ✅ Команда /mood добавлена")
        
        # КОМАНДЫ /chat и /ai
        self.application.add_handler(CommandHandler("chat", self.safe_start_chat))
        self.application.add_handler(CommandHandler("ai", self.safe_start_chat))
        logger.info("  ✅ Команды /chat и /ai добавлены")
        
        # ТЕКСТОВЫЕ СООБЩЕНИЯ
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.safe_handle_text
        ))
        logger.info("  ✅ Обработчик текстовых сообщений добавлен")
        
        # НЕИЗВЕСТНЫЕ КОМАНДЫ
        self.application.add_handler(MessageHandler(
            filters.COMMAND,
            self.safe_handle_unknown
        ))
        logger.info("  ✅ Обработчик неизвестных команд добавлен")
        
        logger.info("✅ Все обработчики успешно настроены")
    
    # === БЕЗОПАСНЫЕ ОБРАБОТЧИКИ (НЕ ЛОМАЮТ БОТА) ===
    
    async def safe_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """БЕЗОПАСНЫЙ обработчик /start"""
        try:
            await start(update, context)
        except Exception as e:
            logger.error(f"Ошибка в safe_start: {e}")
            await update.message.reply_text(
                "✅ *MindMate Bot запущен!*\n\n"
                "Я ваш психологический помощник.\n"
                "Используйте /help для списка команд.",
                parse_mode='Markdown'
            )
    
    async def safe_show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            await show_help(update, context)
        except Exception as e:
            logger.error(f"Ошибка в safe_show_help: {e}")
            await update.message.reply_text(
                "📋 *Доступные команды:*\n"
                "/start - Запуск бота\n"
                "/help - Помощь\n"
                "/mood - Настроение\n"
                "/stats - Статистика\n"
                "/chat - Чат с ИИ\n"
                "/crisis - Экстренная помощь",
                parse_mode='Markdown'
            )
    
    async def safe_handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            await handle_text_message(update, context)
        except Exception as e:
            logger.error(f"Ошибка в safe_handle_text: {e}")
            text = update.message.text[:100]
            await update.message.reply_text(
                f"📝 Вы написали: *{text}*\n\n"
                "Я получил ваше сообщение!",
                parse_mode='Markdown'
            )
    
    async def safe_start_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            await start_chat(update, context)
        except Exception as e:
            logger.error(f"Ошибка в safe_start_chat: {e}")
            await update.message.reply_text(
                "💬 *Режим чата с ИИ*\n\n"
                "Напишите ваш вопрос или тему для обсуждения.",
                parse_mode='Markdown'
            )
    
    async def safe_log_mood(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            await log_mood_command(update, context)
        except Exception as e:
            logger.error(f"Ошибка в safe_log_mood: {e}")
            await update.message.reply_text(
                "📊 *Оцените ваше настроение от 1 до 10:*\n"
                "1 - Очень плохо\n"
                "10 - Отлично!\n\n"
                "Напишите просто цифру.",
                parse_mode='Markdown'
            )
    
    async def safe_show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            await show_stats(update, context)
        except Exception as e:
            logger.error(f"Ошибка в safe_show_stats: {e}")
            await update.message.reply_text(
                "📊 *Статистика*\n\n"
                "У вас пока нет записей.\n"
                "Начните с команды /mood!",
                parse_mode='Markdown'
            )
    
    async def safe_handle_crisis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            await handle_crisis_situation(update, context)
        except Exception as e:
            logger.error(f"Ошибка в safe_handle_crisis: {e}")
            await update.message.reply_text(
                "🚨 *Экстренная помощь:*\n\n"
                "Телефон доверия: 8-800-2000-122\n"
                "Скорая помощь: 103",
                parse_mode='Markdown'
            )
    
    async def safe_handle_unknown(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            await handle_unknown(update, context)
        except Exception as e:
            logger.error(f"Ошибка в safe_handle_unknown: {e}")
            await update.message.reply_text(
                "🤔 Я не понял эту команду.\n"
                "Используйте /help для списка команд."
            )
    
    def setup_error_handler(self):
        """Настройка глобального обработчика ошибок"""
        
        async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Обработчик ошибок, который не ломает бота"""
            try:
                error_msg = str(context.error) if context.error else "Неизвестная ошибка"
                logger.error(f"❌ Ошибка в боте: {error_msg}")
                
                # Отправляем пользователю сообщение
                if update and update.effective_message:
                    await update.effective_message.reply_text(
                        "⚠️ Произошла ошибка. Пожалуйста, попробуйте еще раз.",
                        parse_mode='Markdown'
                    )
            except Exception as e:
                logger.error(f"❌ Ошибка в обработчике ошибок: {e}")
        
        self.application.add_error_handler(error_handler)
        logger.info("✅ Обработчик ошибок настроен")
    
    def run(self):
        """ГЛАВНЫЙ МЕТОД ЗАПУСКА БОТА"""
        try:
            # ПОЛУЧАЕМ ТОКЕН
            TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
            
            if not TOKEN:
                logger.error("❌ TELEGRAM_BOT_TOKEN не найден!")
                logger.error("Добавьте токен в Render Dashboard → Environment Variables")
                logger.info("Пример: TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz")
                return
            
            logger.info(f"✅ Токен найден (первые 10 символов): {TOKEN[:10]}...")
            
            # ПРОВЕРЯЕМ СРЕДУ
            is_render = os.environ.get('RENDER') is not None
            environment = "🌐 Render.com" if is_render else "💻 Локальная разработка"
            logger.info(f"Среда выполнения: {environment}")
            
            # ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ (БЕЗ ОСТАНОВКИ ПРИ ОШИБКЕ)
            try:
                if DB_AVAILABLE:
                    if db_manager.init_db():
                        logger.info("✅ База данных инициализирована")
                    else:
                        logger.warning("⚠️ Проблема с инициализацией БД, но бот продолжит работу")
                else:
                    logger.warning("⚠️ База данных недоступна, бот будет работать без сохранения данных")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка инициализации БД: {e}")
                logger.warning("Бот продолжит работу без базы данных")
            
            # СОЗДАЕМ ПРИЛОЖЕНИЕ
            logger.info("🛠️ Создание Application...")
            self.application = Application.builder().token(TOKEN).build()
            
            # НАСТРАИВАЕМ ОБРАБОТЧИКИ
            self.setup_handlers()
            self.setup_error_handler()
            
            # ЗАПУСКАЕМ БОТА
            logger.info("=" * 60)
            logger.info("🎯 БОТ ЗАПУЩЕН И ГОТОВ К РАБОТЕ!")
            logger.info("=" * 60)
            
            # ПАРАМЕТРЫ POLLING ДЛЯ RENDER
            self.application.run_polling(
                drop_pending_updates=True,
                timeout=30,
                read_timeout=30,
                connect_timeout=30,
                pool_timeout=30,
                close_loop=False  # ВАЖНО ДЛЯ RENDER!
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


def main():
    """ТОЧКА ВХОДА"""
    logger.info("=" * 60)
    logger.info("🧠 ЗАПУСК MINDMATE BOT")
    logger.info("=" * 60)
    
    # ПРОВЕРКА ВЕРСИИ PYTHON
    if sys.version_info < (3, 9):
        logger.error(f"❌ Требуется Python 3.9+, текущая версия: {sys.version}")
        return
    
    # ЗАПУСК
    bot = MindMateBot()
    bot.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 Приложение остановлено пользователем")
    except Exception as e:
        logger.error(f"❌ Необработанная ошибка: {e}")
