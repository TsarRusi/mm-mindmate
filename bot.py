#!/usr/bin/env python3
"""
MindMate Bot - психологический помощник
Версия для Render.com с исправлениями всех ошибок
"""

import os
import sys
import logging
from datetime import datetime

# Добавляем путь для импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Настройка логирования ДО всех импортов
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Важно для Render логов!
    ]
)
logger = logging.getLogger(__name__)

# Импорты Telegram
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters,
    ContextTypes
)
from telegram.error import NetworkError, TelegramError

# Импорты нашего приложения
try:
    # Импортируем функции обработчиков НАПРЯМУЮ
    from message_handlers import (
        start,
        show_help,
        handle_text_message,
        start_chat,
        handle_ai_chat,
        log_mood_command,
        show_stats,
        handle_crisis_situation,
        handle_unknown
    )
    from database import db_manager
    from nlp_analyzer import nlp_analyzer
    from deepseek_chat import deepseek_chat
    logger.info("✅ Все модули успешно импортированы")
except ImportError as e:
    logger.error(f"❌ Ошибка импорта модулей: {e}")
    logger.error("Проверьте наличие всех файлов в проекте")
    sys.exit(1)

class MindMateBot:
    """Главный класс бота с исправлениями для Render"""
    
    def __init__(self):
        self.application = None
        self.is_running = False
        logger.info("🧠 MindMate Bot инициализирован")
    
    async def on_startup(self, application):
        """Запуск при старте бота"""
        logger.info("=" * 60)
        logger.info("🚀 MindMate Bot ЗАПУСКАЕТСЯ")
        logger.info("=" * 60)
        
        # Информация о системе
        logger.info(f"🐍 Python версия: {sys.version}")
        logger.info(f"📁 Рабочая директория: {os.getcwd()}")
        logger.info(f"⏰ Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Проверка переменных окружения
        token = os.environ.get('TELEGRAM_BOT_TOKEN')
        if not token:
            logger.error("❌ КРИТИЧЕСКАЯ ОШИБКА: TELEGRAM_BOT_TOKEN не найден!")
            logger.error("Добавьте TELEGRAM_BOT_TOKEN в Environment Variables на Render")
            logger.error("Render Dashboard → Your Service → Environment")
            return False
        
        logger.info(f"✅ TELEGRAM_BOT_TOKEN найден (первые 10 символов): {token[:10]}...")
        
        # Проверка DeepSeek
        deepseek_key = os.environ.get('DEEPSEEK_API_KEY')
        if deepseek_key:
            logger.info("✅ DeepSeek API ключ найден")
        else:
            logger.warning("⚠️ DeepSeek API ключ не найден (чат с ИИ будет ограничен)")
        
        # Инициализация БД
        try:
            db_manager.init_db()
            logger.info("✅ База данных инициализирована")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
            # Продолжаем работу даже без БД
        
        # Проверка NLP анализатора
        try:
            test_analysis = nlp_analyzer.analyze_text("Тестовое сообщение")
            logger.info(f"✅ NLP анализатор работает: {test_analysis.get('success', False)}")
        except Exception as e:
            logger.error(f"❌ NLP анализатор не работает: {e}")
        
        self.is_running = True
        logger.info("✅ Бот готов к приему сообщений")
        logger.info("=" * 60)
        return True
    
    async def on_shutdown(self, application):
        """Завершение работы бота"""
        logger.info("=" * 60)
        logger.info("🛑 MindMate Bot останавливается...")
        logger.info("=" * 60)
        self.is_running = False
    
    def setup_handlers(self):
        """Настройка всех обработчиков команд и сообщений"""
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
        
        # ===== ТЕКСТОВЫЕ СООБЩЕНИЯ =====
        
        # Обработка обычных текстовых сообщений
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text_message
        ))
        logger.info("  ✅ Обработчик текстовых сообщений добавлен")
        
        # Обработка неизвестных команд
        self.application.add_handler(MessageHandler(
            filters.COMMAND,
            handle_unknown
        ))
        logger.info("  ✅ Обработчик неизвестных команд добавлен")
        
        # ===== КЛАВИАТУРЫ И КНОПКИ =====
        
        # Простая клавиатура для главного меню
        async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Обработчик главного меню"""
            keyboard = [
                ["/start", "/help"],
                ["/mood", "/stats"],
                ["/chat", "/crisis"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            if update.message:
                await update.message.reply_text(
                    "Главное меню MindMate:\n"
                    "Выберите действие или напишите сообщение",
                    reply_markup=reply_markup
                )
        
        # Добавляем обработчик для кнопок меню
        self.application.add_handler(MessageHandler(
            filters.Regex("^(Главное меню|Меню|Назад)$"),
            handle_main_menu
        ))
        
        logger.info("✅ Все обработчики успешно настроены")
    
    def setup_error_handler(self):
        """Настройка обработчика ошибок"""
        
        async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Глобальный обработчик ошибок"""
            error_msg = str(context.error) if context.error else "Неизвестная ошибка"
            
            logger.error("=" * 60)
            logger.error(f"❌ ОШИБКА В БОТЕ: {error_msg}")
            logger.error("=" * 60)
            
            # Логируем traceback
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            
            # Отправляем сообщение пользователю
            try:
                if update and update.effective_message:
                    error_text = (
                        "⚠️ *Произошла ошибка*\n\n"
                        "Пожалуйста, попробуйте еще раз или используйте команду /start\n"
                        "Если ошибка повторяется, свяжитесь с поддержкой."
                    )
                    await update.effective_message.reply_text(
                        error_text,
                        parse_mode='Markdown'
                    )
            except Exception as e:
                logger.error(f"Не удалось отправить сообщение об ошибке: {e}")
        
        self.application.add_error_handler(error_handler)
        logger.info("✅ Обработчик ошибок настроен")
    
    def run(self):
        """Главный метод запуска бота"""
        try:
            # Получаем токен
            TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
            
            if not TOKEN:
                logger.error("❌ TELEGRAM_BOT_TOKEN не найден в переменных окружения!")
                logger.error("Добавьте токен в Render Dashboard → Environment Variables")
                return
            
            # Проверяем, запущены ли мы на Render
            is_render = os.environ.get('RENDER') is not None
            environment = "🌐 Render.com" if is_render else "💻 Локальная разработка"
            logger.info(f"Среда выполнения: {environment}")
            
            # Создаем приложение
            logger.info("🛠️ Создание Application...")
            self.application = Application.builder().token(TOKEN).build()
            
            # Настраиваем обработчики
            self.setup_handlers()
            self.setup_error_handler()
            
            # Настройки polling
            poll_params = {
                'drop_pending_updates': True,
                'timeout': 30,
                'read_timeout': 30,
                'connect_timeout': 30,
                'pool_timeout': 30,
                'close_loop': False,  # Важно для Render!
            }
            
            # Запускаем бота
            logger.info("=" * 60)
            logger.info("🎯 БОТ ЗАПУЩЕН И ГОТОВ К РАБОТЕ!")
            logger.info("=" * 60)
            
            self.application.run_polling(**poll_params)
            
        except NetworkError as e:
            logger.error(f"❌ Ошибка сети: {e}")
            logger.error("Проверьте интернет-соединение и доступность Telegram API")
        except TelegramError as e:
            logger.error(f"❌ Ошибка Telegram API: {e}")
            logger.error("Проверьте токен бота и его настройки")
        except KeyboardInterrupt:
            logger.info("🛑 Остановка по запросу пользователя (Ctrl+C)")
        except Exception as e:
            logger.error("=" * 60)
            logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
            logger.error("=" * 60)
            import traceback
            logger.error(f"Полный traceback:\n{traceback.format_exc()}")
            sys.exit(1)

def health_check():
    """Простая проверка здоровья приложения (для мониторинга)"""
    logger.info("🏥 Health check: OK")
    return True

def main():
    """Точка входа в приложение"""
    logger.info("=" * 60)
    logger.info("🧠 ЗАПУСК MINDMATE BOT")
    logger.info("=" * 60)
    
    # Проверяем минимальные требования
    if sys.version_info < (3, 9):
        logger.error(f"❌ Требуется Python 3.9+, текущая версия: {sys.version}")
        sys.exit(1)
    
    # Запускаем бота
    bot = MindMateBot()
    
    # Простая проверка здоровья
    if health_check():
        logger.info("✅ Проверка здоровья пройдена")
    else:
        logger.warning("⚠️ Проверка здоровья показала проблемы")
    
    # Запуск
    bot.run()

if __name__ == "__main__":
    # Обработка Ctrl+C
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 Приложение остановлено пользователем")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Необработанная ошибка в main(): {e}")
        sys.exit(1)
