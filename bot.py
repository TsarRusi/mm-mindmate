import os
import sys
import logging
import asyncio
from datetime import datetime

# Добавляем путь для импортов на Render
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    ConversationHandler,
    filters
)
from telegram.error import NetworkError, TelegramError

# Настройка логирования для Render
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Важно для Render логов!
    ]
)
logger = logging.getLogger(__name__)

# Импорты для вашего бота
try:
    from config import settings
    from database import db_manager
    from message_handlers import handlers
except ImportError as e:
    logger.error(f"Ошибка импорта: {e}")
    logger.error("Проверьте наличие всех файлов")
    sys.exit(1)

class MindMateBotRender:
    """Версия бота оптимизированная для Render"""
    
    def __init__(self):
        self.application = None
        
    async def on_startup(self, app):
        """Запуск при старте"""
        logger.info("=" * 50)
        logger.info("🚀 MindMate Bot запускается на Render")
        logger.info(f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"🐍 Python: {sys.version}")
        logger.info(f"📁 Рабочая директория: {os.getcwd()}")
        logger.info("=" * 50)
        
        # Инициализация БД
        try:
            db_manager.init_db()
            logger.info("✅ База данных инициализирована")
        except Exception as e:
            logger.error(f"❌ Ошибка БД: {e}")
            # Продолжаем работу, даже если БД не работает
    
    async def on_shutdown(self, app):
        """Остановка бота"""
        logger.info("🛑 MindMate Bot останавливается...")
    
    def setup_handlers(self):
        """Настройка обработчиков (упрощенная версия)"""
        
        # Базовые команды
        self.application.add_handler(CommandHandler("start", handlers.start))
        self.application.add_handler(CommandHandler("help", handlers.show_help))
        self.application.add_handler(CommandHandler("crisis", handlers.handle_crisis_situation))
        
        # Основное меню
        from telegram import ReplyKeyboardMarkup
        
        async def handle_main_menu(update, context):
            keyboard = [
                ["📊 Настроение", "💬 Чат с ИИ"],
                ["🧘 Упражнения", "📈 Статистика"],
                ["⚙️ Настройки", "❓ Помощь"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(
                "Главное меню MindMate:",
                reply_markup=reply_markup
            )
        
        self.application.add_handler(MessageHandler(
            filters.Regex("^(📊 Настроение|💬 Чат с ИИ|🧘 Упражнения|📈 Статистика|⚙️ Настройки|❓ Помощь)$"),
            handle_main_menu
        ))
        
        # Обработка текстовых сообщений
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handlers.handle_unknown
        ))
        
        logger.info("✅ Обработчики настроены")
    
    def run(self):
        """Запуск бота на Render"""
        try:
            # Получаем токен из переменных окружения Render
            TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
            
            if not TOKEN:
                logger.error("❌ TELEGRAM_BOT_TOKEN не найден!")
                logger.error("Добавьте TELEGRAM_BOT_TOKEN в Environment Variables на Render")
                logger.error("Render Dashboard -> Your Service -> Environment")
                sys.exit(1)
            
            # Проверяем наличие ключа DeepSeek (опционально)
            DEEPSEEK_KEY = os.environ.get('DEEPSEEK_API_KEY')
            if DEEPSEEK_KEY:
                logger.info("✅ DeepSeek API ключ найден")
            else:
                logger.warning("⚠️ DeepSeek API ключ не найден (функция чата будет ограничена)")
            
            # Создаем Application
            self.application = Application.builder() \
                .token(TOKEN) \
                .post_init(self.on_startup) \
                .post_shutdown(self.on_shutdown) \
                .build()
            
            # Настраиваем обработчики
            self.setup_handlers()
            
            # Обработчик ошибок
            async def error_handler(update, context):
                logger.error(f"Ошибка: {context.error}", exc_info=True)
            
            self.application.add_error_handler(error_handler)
            
            # Запускаем бота с настройками для Render
            logger.info("✅ Бот готов к запуску")
            logger.info(f"🔑 Токен: {TOKEN[:15]}...")
            logger.info("⏳ Запускаю polling...")
            
            self.application.run_polling(
                drop_pending_updates=True,
                timeout=30,
                read_timeout=30,
                connect_timeout=30,
                pool_timeout=30
            )
            
        except NetworkError as e:
            logger.error(f"❌ Ошибка сети: {e}")
        except TelegramError as e:
            logger.error(f"❌ Ошибка Telegram API: {e}")
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
            sys.exit(1)

def main():
    """Точка входа"""
    bot = MindMateBotRender()
    bot.run()

if __name__ == "__main__":
    # Проверяем, что мы на Render
    if os.environ.get('RENDER'):
        logger.info("🌐 Среда: Render.com")
    else:
        logger.info("💻 Среда: Локальная разработка")
    
    main()
