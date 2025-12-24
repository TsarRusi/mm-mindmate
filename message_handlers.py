# === ИСПРАВЛЕННЫЕ ОБРАБОТЧИКИ ===
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from database import db_manager
from nlp_analyzer import nlp_analyzer
from deepseek_chat import deepseek_chat

logger = logging.getLogger(__name__)

# ВСЕ функции должны начинаться с async def!
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Сохраняем пользователя в БД
    db_user = db_manager.add_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name
    )
    
    welcome_text = f"""🧠 *Добро пожаловать в MindMate, {user.first_name}!*..."""
    
    keyboard = [
        ["📊 Настроение", "💬 Чат с ИИ"],
        ["🧘 Упражнения", "📈 Статистика"],
        ["❓ Помощь"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    # ВСЕГДА добавляйте await перед reply_text!
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать помощь"""
    help_text = """*🆘 Помощь по MindMate Bot*..."""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    user_message = update.message.text
    
    # Сохраняем пользователя если еще нет
    user = update.effective_user
    db_user = db_manager.add_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name
    )
    
    # Анализируем текст
    analysis = nlp_analyzer.analyze_text(user_message)
    
    # Сохраняем в лог
    db_manager.add_mood_log(
        user_id=db_user.id,
        mood_score=analysis.get('sentiment', {}).get('score', 0.5),
        message=user_message
    )
    
    if analysis.get('is_crisis'):
        response = """🚨 *Обнаружены тревожные слова!*..."""
        await update.message.reply_text(response, parse_mode='Markdown')
        return
    
    # Если не кризис - показываем анализ
    summary = nlp_analyzer.get_summary(analysis)
    
    response = f"""{summary}..."""
    
    await update.message.reply_text(response, parse_mode='Markdown')

# Остальные функции ТОЖЕ исправьте:
async def start_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💬 *Режим чата с ИИ*...", parse_mode='Markdown')

async def handle_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await update.message.chat.send_action(action="typing")
    result = await deepseek_chat.get_response(user_message)
    await update.message.reply_text(result['response'], parse_mode='HTML')

async def log_mood_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 *Оцените ваше настроение...*", parse_mode='Markdown')

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # ... ваш код
    await update.message.reply_text(stat_text, parse_mode='Markdown')

async def handle_crisis_situation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚨 *ЭКСТРЕННАЯ ПОМОЩЬ*...", parse_mode='Markdown')

async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Я не совсем понял ваше сообщение. 😕...")

# Экспортируем КАК ЕСТЬ - без создания класса
__all__ = ['start', 'show_help', 'handle_text_message', 'start_chat', 
           'handle_ai_chat', 'log_mood_command', 'show_stats', 
           'handle_crisis_situation', 'handle_unknown']
