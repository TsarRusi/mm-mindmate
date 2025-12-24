#!/usr/bin/env python3
"""
MindMate Bot - психологический помощник
ПОЛНОСТЬЮ РАБОЧАЯ ВЕРСИЯ С КНОПКАМИ И ОФОРМЛЕНИЕМ
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

# 1. Импортируем Telegram
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
    from message_handlers import (
        start,
        show_help,
        handle_text_message,
        handle_mood_button,
        handle_ai_chat_button,
        handle_exercises_button,
        handle_stats_button,
        handle_settings_button,
        handle_back_button,
        log_mood_command,
        start_chat,
        show_stats,
        handle_crisis_situation,
        handle_unknown
    )
    logger.info("✅ Все обработчики импортированы")
except ImportError as e:
    logger.error(f"❌ Ошибка импорта обработчиков: {e}")
    # Создаем простые заглушки
    async def start(update, context):
        await update.message.reply_text("✅ MindMate Bot запущен! Используйте /help")
    async def show_help(update, context):
        await update.message.reply_text("Помощь: /start, /help, /mood, /stats, /chat, /crisis")
    async def handle_text_message(update, context):
        await update.message.reply_text(f"Сообщение получено: {update.message.text[:50]}...")
    
    # Заглушки для обработчиков кнопок
    async def handle_mood_button(update, context):
        await update.message.reply_text("📊 Нажмите кнопку настроения или напишите цифру от 1 до 10")
    async def handle_ai_chat_button(update, context):
        await update.message.reply_text("💬 Напишите ваш вопрос для ИИ")
    async def handle_exercises_button(update, context):
        await update.message.reply_text("🧘 Выберите упражнение для релаксации")
    async def handle_stats_button(update, context):
        await update.message.reply_text("📈 Статистика будет доступна после нескольких записей")
    async def handle_settings_button(update, context):
        await update.message.reply_text("⚙️ Настройки будут доступны в следующих версиях")
    async def handle_back_button(update, context):
        await update.message.reply_text("↩️ Возвращаемся в главное меню")
    async def log_mood_command(update, context):
        await update.message.reply_text("Напишите цифру от 1 до 10")
    async def start_chat(update, context):
        await update.message.reply_text("💬 Напишите ваш вопрос")
    async def show_stats(update, context):
        await update.message.reply_text("📊 Статистика")
    async def handle_crisis_situation(update, context):
        await update.message.reply_text("🚨 Телефон доверия: 8-800-2000-122")
    async def handle_unknown(update, context):
        await update.message.reply_text("Используйте /help для списка команд")

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
    """Бот с полной функциональностью и обработкой кнопок"""
    
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
        """Настройка ВСЕХ обработчиков - КОМАНДЫ И КНОПКИ"""
        logger.info("🔄 Настройка обработчиков...")
        
        # ===== КОМАНДЫ =====
        
        # /start - главная команда
        self.application.add_handler(CommandHandler("start", start))
        logger.info("  ✅ Команда /start добавлена")
        
        # /help - помощь
        self.application.add_handler(CommandHandler("help", show_help))
        logger.info("  ✅ Команда /help добавлена")
        
        # /crisis - экстренная помощь
        self.application.add_handler(CommandHandler("crisis", handle_crisis_situation))
        logger.info("  ✅ Команда /crisis добавлена")
        
        # /stats - статистика
        self.application.add_handler(CommandHandler("stats", show_stats))
        logger.info("  ✅ Команда /stats добавлена")
        
        # /mood - запись настроения
        self.application.add_handler(CommandHandler("mood", log_mood_command))
        logger.info("  ✅ Команда /mood добавлена")
        
        # /chat и /ai - чат с ИИ
        self.application.add_handler(CommandHandler("chat", start_chat))
        self.application.add_handler(CommandHandler("ai", start_chat))
        logger.info("  ✅ Команды /chat и /ai добавлены")
        
        # ===== ОБРАБОТЧИКИ КНОПОК =====
        
        # 📊 Настроение
        self.application.add_handler(MessageHandler(
            filters.Regex("^(📊 Настроение|Настроение|Оценить настроение|Мое настроение)$"),
            handle_mood_button
        ))
        logger.info("  ✅ Обработчик кнопки 'Настроение' добавлен")
        
        # 💬 Чат с ИИ
        self.application.add_handler(MessageHandler(
            filters.Regex("^(💬 Чат с ИИ|Чат с ИИ|Поговорить с ИИ|Общение с ИИ)$"),
            handle_ai_chat_button
        ))
        logger.info("  ✅ Обработчик кнопки 'Чат с ИИ' добавлен")
        
        # 🧘 Упражнения
        self.application.add_handler(MessageHandler(
            filters.Regex("^(🧘 Упражнения|Упражнения|Релаксация|Медитация)$"),
            handle_exercises_button
        ))
        logger.info("  ✅ Обработчик кнопки 'Упражнения' добавлен")
        
        # 📈 Статистика
        self.application.add_handler(MessageHandler(
            filters.Regex("^(📈 Статистика|Статистика|Моя статистика|Аналитика)$"),
            handle_stats_button
        ))
        logger.info("  ✅ Обработчик кнопки 'Статистика' добавлен")
        
        # ⚙️ Настройки
        self.application.add_handler(MessageHandler(
            filters.Regex("^(⚙️ Настройки|Настройки|Настройки бота)$"),
            handle_settings_button
        ))
        logger.info("  ✅ Обработчик кнопки 'Настройки' добавлен")
        
        # ↩️ Назад
        self.application.add_handler(MessageHandler(
            filters.Regex("^(↩️ Назад в меню|↩️ Назад|Вернуться|Назад в меню|Главное меню)$"),
            handle_back_button
        ))
        logger.info("  ✅ Обработчик кнопки 'Назад' добавлен")
        
        # ===== СПЕЦИАЛЬНЫЕ КНОПКИ =====
        
        # Оценки настроения (цифры с эмодзи)
        mood_pattern = r"^(1 😭|2 😢|3 😔|4 😕|5 😐|6 🙂|7 👍|8 😊|9 🤩|10 😍|1|2|3|4|5|6|7|8|9|10)$"
        self.application.add_handler(MessageHandler(
            filters.Regex(mood_pattern),
            handle_text_message  # Будет обработано в основном обработчике
        ))
        logger.info("  ✅ Обработчик оценок настроения добавлен")
        
        # Упражнения (конкретные)
        exercises_pattern = r"^(🧘 Дыхание|🌿 Медитация|💪 Релаксация|📝 Благодарность|🎵 Музыка)$"
        self.application.add_handler(MessageHandler(
            filters.Regex(exercises_pattern),
            handle_text_message  # Будет обработано в основном обработчике
        ))
        logger.info("  ✅ Обработчик конкретных упражнений добавлен")
        
        # ===== ОБЩИЙ ТЕКСТ =====
        
        # Обработка обычных текстовых сообщений
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text_message
        ))
        logger.info("  ✅ Общий обработчик текстовых сообщений добавлен")
        
        # ===== НЕИЗВЕСТНЫЕ КОМАНДЫ =====
        
        self.application.add_handler(MessageHandler(
            filters.COMMAND,
            handle_unknown
        ))
        logger.info("  ✅ Обработчик неизвестных команд добавлен")
        
        logger.info("✅ Все обработчики успешно настроены")
    
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
                        "⚠️ *Произошла ошибка.*\n\n"
                        "Пожалуйста, попробуйте еще раз или используйте /start\n"
                        "Если ошибка повторяется, свяжитесь с поддержкой.",
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
        logger.info(f"🐍 Python версия: {sys.version}")
        logger.info(f"📁 Рабочая директория: {os.getcwd()}")
        logger.info(f"⏰ Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Проверка среды
        is_render = os.environ.get('RENDER') is not None
        environment = "🌐 Render.com" if is_render else "💻 Локальная разработка"
        logger.info(f"Среда выполнения: {environment}")
        
        # Проверка модулей
        logger.info(f"📊 База данных: {'✅ Доступна' if hasattr(db_manager, 'init_db') else '⚠️ Заглушка'}")
        logger.info(f"🧠 NLP анализ: {'✅ Доступен' if NLP_AVAILABLE else '⚠️ Недоступен'}")
        logger.info(f"🤖 DeepSeek AI: {'✅ Доступен' if DEEPSEEK_AVAILABLE else '⚠️ Недоступен'}")
        
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
