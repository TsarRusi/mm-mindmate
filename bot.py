import logging
import asyncio
from datetime import datetime, time
import pytz

from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    ConversationHandler,
    filters
)
from telegram.error import NetworkError

from config import settings
from database import db_manager
from message_handlers import handlers, MOOD_INPUT, AI_CHAT
from utils import RateLimiter

logger = logging.getLogger(__name__)

class MindMateBot:
    """Главный класс бота."""
    
    def __init__(self):
        self.application = None
        self.rate_limiter = RateLimiter(max_requests=20, period=3600)
        
    async def on_startup(self, application: Application) -> None:
        """Действия при запуске бота."""
        logger.info("🚀 MindMate Bot запускается...")
        
        # Инициализация БД
        try:
            db_manager.init_db()
            logger.info("✅ База данных инициализирована")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
        
        # Настройка планировщика задач
        job_queue = application.job_queue
        
        if job_queue and settings.ENABLE_REMINDERS:
            # Ежедневные напоминания
            try:
                reminder_time = datetime.strptime(settings.DAILY_CHECKIN_TIME, "%H:%M").time()
                job_queue.run_daily(
                    self.send_daily_reminders,
                    time=reminder_time,
                    days=tuple(range(7))  # Каждый день
                )
                logger.info(f"✅ Напоминания настроены на {settings.DAILY_CHECKIN_TIME}")
            except Exception as e:
                logger.error(f"❌ Ошибка настройки напоминаний: {e}")
        
        logger.info("✅ MindMate Bot успешно запущен!")
        logger.info(f"👥 Администраторы: {settings.ADMIN_IDS}")
        logger.info(f"🌐 Временная зона: {settings.TIMEZONE}")
        logger.info(f"🗣️ Язык: {settings.LANGUAGE}")
    
    async def on_shutdown(self, application: Application) -> None:
        """Действия при остановке бота."""
        logger.info("🛑 MindMate Bot останавливается...")
        
        # Очистка ресурсов
        if application.job_queue:
            application.job_queue.stop()
        
        logger.info("✅ MindMate Bot остановлен")
    
    async def send_daily_reminders(self, context) -> None:
        """Отправка ежедневных напоминаний."""
        logger.info("📅 Отправка ежедневных напоминаний...")
        
        # Здесь должна быть логика получения пользователей с включенными напоминаниями
        # и отправки им сообщений
        
        # Пример:
        # users = get_users_with_reminders()
        # for user in users:
        #     try:
        #         await context.bot.send_message(
        #             chat_id=user.telegram_id,
        #             text="Напоминание: как твое настроение сегодня?",
        #             reply_markup=get_mood_keyboard()
        #         )
        #     except Exception as e:
        #         logger.error(f"Ошибка отправки напоминания пользователю {user.telegram_id}: {e}")
        
        logger.info(f"✅ Напоминания отправлены")
    
    def setup_handlers(self) -> None:
        """Настройка обработчиков."""
        # ConversationHandler для отслеживания настроения
        mood_conv_handler = ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex("^📊 Записать настроение$"), handlers.ask_mood),
                CallbackQueryHandler(handlers.ask_mood, pattern="^back_to_mood$")
            ],
            states={
                MOOD_INPUT: [
                    CallbackQueryHandler(handlers.handle_mood_score, pattern="^mood_"),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_mood_text)
                ]
            },
            fallbacks=[
                CommandHandler("cancel", handlers.show_main_menu),
                CallbackQueryHandler(handlers.show_main_menu, pattern="^back_to_main$")
            ],
            allow_reentry=True
        )
        
        # ConversationHandler для чата с ИИ
        ai_conv_handler = ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex("^💬 Поговорить с ИИ$"), handlers.show_ai_menu),
                CallbackQueryHandler(handlers.show_ai_menu, pattern="^back_to_ai$")
            ],
            states={
                AI_CHAT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_ai_message)
                ]
            },
            fallbacks=[
                CallbackQueryHandler(handlers.end_ai_chat, pattern="^ai_end_session$"),
                CommandHandler("cancel", handlers.show_main_menu)
            ],
            allow_reentry=True
        )
        
        # Базовые обработчики
        self.application.add_handler(CommandHandler("start", handlers.start))
        self.application.add_handler(CommandHandler("help", handlers.show_help))
        self.application.add_handler(CommandHandler("crisis", handlers.handle_crisis_situation))
        self.application.add_handler(CommandHandler("stats", handlers.show_statistics_menu))
        self.application.add_handler(CommandHandler("settings", handlers.show_settings_menu))
        
        # Обработчики меню
        self.application.add_handler(MessageHandler(
            filters.Regex("^(🧘 Упражнения|📈 Статистика|⚙️ Настройки|❓ Помощь)$"), 
            handlers.handle_main_menu
        ))
        
        # Conversation handlers
        self.application.add_handler(mood_conv_handler)
        self.application.add_handler(ai_conv_handler)
        
        # Callback handlers
        self.application.add_handler(CallbackQueryHandler(handlers.handle_callback))
        
        # Обработчик неизвестных сообщений
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            handlers.handle_unknown
        ))
        
        logger.info("✅ Обработчики настроены")
    
    async def error_handler(self, update: object, context) -> None:
        """Обработчик ошибок."""
        logger.error(f"Ошибка: {context.error}", exc_info=context.error)
        
        # Отправляем сообщение об ошибке пользователю
        if update and hasattr(update, 'effective_user'):
            try:
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text="⚠️ Произошла ошибка. Пожалуйста, попробуйте позже."
                )
            except:
                pass
        
        # Уведомляем администраторов
        for admin_id in settings.ADMIN_IDS:
            try:
                error_msg = f"❌ Ошибка в боте:\n\n{type(context.error).__name__}: {context.error}"
                await context.bot.send_message(chat_id=admin_id, text=error_msg[:4000])
            except:
                pass
    
    def run(self) -> None:
        """Запуск бота."""
        try:
            # Создаем Application
            self.application = Application.builder()\
                .token(settings.TELEGRAM_BOT_TOKEN)\
                .post_init(self.on_startup)\
                .post_shutdown(self.on_shutdown)\
                .build()
            
            # Настраиваем обработчики
            self.setup_handlers()
            
            # Добавляем обработчик ошибок
            self.application.add_error_handler(self.error_handler)
            
            # Запускаем бота
            logger.info("=" * 50)
            logger.info("🤖 MindMate Bot запущен")
            logger.info(f"⏰ Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"🌐 Timezone: {settings.TIMEZONE}")
            logger.info("⏹️  Остановить: Ctrl+C")
            logger.info("=" * 50)
            
            self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
                close_loop=False
            )
            
        except Exception as e:
            logger.critical(f"Критическая ошибка при запуске бота: {e}", exc_info=True)
            raise

def main():
    """Точка входа."""
    bot = MindMateBot()
    bot.run()

if __name__ == "__main__":
    main()