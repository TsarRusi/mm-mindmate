"""
Файл с клавиатурами для бота
"""

from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard():
    """Основная клавиатура"""
    keyboard = [
        ["📊 Настроение", "💬 Чат с ИИ"],
        ["🧘 Упражнения", "📈 Статистика"],
        ["⚙️ Настройки", "❓ Помощь"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, selective=True)

def get_mood_keyboard():
    """Клавиатура для оценки настроения"""
    keyboard = [
        ["1 😭", "2 😢", "3 😔", "4 😕", "5 😐"],
        ["6 🙂", "7 👍", "8 😊", "9 🤩", "10 😍"],
        ["↩️ Назад в меню"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_exercises_keyboard():
    """Клавиатура упражнений"""
    keyboard = [
        ["🧘 Дыхание", "🌿 Медитация"],
        ["💪 Релаксация", "📝 Благодарность"],
        ["🎵 Музыка", "↩️ Назад в меню"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_stats_inline_keyboard():
    """Inline клавиатура для статистики"""
    keyboard = [
        [
            InlineKeyboardButton("📅 Сегодня", callback_data="stats_today"),
            InlineKeyboardButton("📆 Неделя", callback_data="stats_week")
        ],
        [
            InlineKeyboardButton("🗓️ Месяц", callback_data="stats_month"),
            InlineKeyboardButton("📊 Все время", callback_data="stats_all")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

__all__ = [
    'get_main_keyboard',
    'get_mood_keyboard',
    'get_exercises_keyboard',
    'get_stats_inline_keyboard'
]
