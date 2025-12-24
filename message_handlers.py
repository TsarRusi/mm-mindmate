"""
Обработчики сообщений для MindMate Bot
КОРОТКАЯ РАБОЧАЯ ВЕРСИЯ
"""

import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# ============ ОБРАБОТЧИКИ ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    try:
        user = update.effective_user
        
        welcome_text = f"""
🧠 *Добро пожаловать в MindMate, {user.first_name}!*

Я ваш психологический помощник.

*Что я умею:*
• Анализировать ваше настроение
• Давать рекомендации
• Вести статистику
• Общаться в чате с ИИ

*Основные команды:*
/start - Перезапуск
/help - Помощь
/mood - Оценить настроение
/stats - Статистика
/chat - Чат с ИИ
/crisis - Экстренная помощь

Просто напишите, как дела! 😊
        """
        
        # Простая клавиатура
        keyboard = [["/help", "/mood"], ["/stats", "/chat"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Ошибка в start: {e}")
        await update.message.reply_text("✅ Бот запущен! Используйте /help")

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    try:
        help_text = """
*🆘 Помощь по MindMate Bot*

*Как работать с ботом:*
1. Напишите сообщение о вашем настроении
2. Используйте команды для разных функций
3. Получайте рекомендации и анализ

*Доступные команды:*
/start - Перезапустить бота
/help - Эта справка
/mood - Записать настроение (1-10)
/chat - Начать диалог с ИИ
/stats - Показать статистику
/crisis - Экстренная помощь

*📞 Телефоны доверия:*
8-800-2000-122 - Единый телефон доверия
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка в show_help: {e}")
        await update.message.reply_text("Используйте: /start, /help, /mood, /stats, /chat, /crisis")

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    try:
        text = update.message.text
        
        # Простой анализ
        if any(word in text.lower() for word in ['плохо', 'грустно', 'устал', 'стресс']):
            response = """
😔 *Похоже, вам нелегко.*

Попробуйте:
1. Сделать глубокий вдох и выдох
2. Выпить стакан воды
3. Немного прогуляться

Можете оценить настроение точнее командой /mood
            """
        elif any(word in text.lower() for word in ['хорошо', 'отлично', 'рад', 'счастлив']):
            response = """
😊 *Отлично, что у вас хорошее настроение!*

Продолжайте в том же духе!
Запишите, что именно вызвало позитивные эмоции.
            """
        else:
            response = f"""
📝 *Я получил ваше сообщение:*

"{text[:100]}..."

Что вы хотите сделать дальше?
• Оценить настроение: /mood
• Посмотреть статистику: /stats
• Пообщаться с ИИ: /chat
            """
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка в handle_text_message: {e}")
        await update.message.reply_text("✅ Сообщение получено!")

async def start_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /chat"""
    try:
        await update.message.reply_text(
            "💬 *Режим чата с ИИ*\n\n"
            "Функция чата с искусственным интеллектом скоро будет добавлена.\n\n"
            "А пока можете:\n"
            "• Написать о вашем настроении\n"
            "• Использовать команду /mood\n"
            "• Посмотреть статистику /stats",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Ошибка в start_chat: {e}")
        await update.message.reply_text("💬 Чат с ИИ скоро будет доступен!")

async def log_mood_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /mood"""
    try:
        await update.message.reply_text(
            "📊 *Оцените ваше настроение от 1 до 10:*\n\n"
            "1 - Очень плохо 😭\n"
            "5 - Нормально 😐\n"
            "10 - Отлично! 😍\n\n"
            "Напишите просто цифру, например: 7",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Ошибка в log_mood_command: {e}")
        await update.message.reply_text("Напишите цифру от 1 до 10")

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats"""
    try:
        await update.message.reply_text(
            "📊 *Ваша статистика*\n\n"
            "Статистика появится после нескольких записей настроения.\n\n"
            "Что делать:\n"
            "1. Используйте /mood для оценки настроения\n"
            "2. Пишите сообщения о вашем состоянии\n"
            "3. Через время здесь появится статистика",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Ошибка в show_stats: {e}")
        await update.message.reply_text("📊 Статистика скоро будет доступна")

async def handle_crisis_situation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /crisis"""
    try:
        await update.message.reply_text(
            "🚨 *ЭКСТРЕННАЯ ПОМОЩЬ*\n\n"
            "*📞 Телефоны доверия (бесплатно):*\n"
            "• 8-800-2000-122 — Единый телефон доверия\n"
            "• 112 — Единый номер экстренных служб\n\n"
            "*🏥 Если нужна срочная помощь:*\n"
            "1. Вызовите скорую помощь (103)\n"
            "2. Обратитесь к близким\n\n"
            "*Вы не одни! Помощь доступна 24/7.*",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Ошибка в handle_crisis_situation: {e}")
        await update.message.reply_text("🚨 Телефон доверия: 8-800-2000-122")

async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Неизвестные команды"""
    try:
        await update.message.reply_text(
            "🤔 *Я не понял эту команду.*\n\n"
            "Используйте:\n"
            "/help - для списка команд\n"
            "/start - для перезапуска\n\n"
            "Или просто напишите сообщение о вашем настроении.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Ошибка в handle_unknown: {e}")
        await update.message.reply_text("Используйте /help для списка команд")

# ============ ЭКСПОРТ ============

__all__ = [
    'start',
    'show_help', 
    'handle_text_message',
    'start_chat',
    'log_mood_command',
    'show_stats',
    'handle_crisis_situation',
    'handle_unknown'
]
