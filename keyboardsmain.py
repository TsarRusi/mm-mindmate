import logging
from typing import List
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Основная клавиатура меню"""
    keyboard = [
        ["📊 Настроение", "💬 Чат с ИИ"],
        ["🧘 Упражнения", "📈 Статистика"],
        ["⚙️ Настройки", "❓ Помощь"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, selective=True)

def get_mood_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для оценки настроения"""
    keyboard = [
        ["1 😭", "2 😢", "3 😔", "4 😕", "5 😐"],
        ["6 🙂", "7 👍", "8 😊", "9 🤩", "10 😍"],
        ["↩️ Назад"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_exercises_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура упражнений"""
    keyboard = [
        ["🧘 Дыхание 4-7-8", "🌿 Медитация 5 мин"],
        ["💪 Прогрессивная релаксация", "📝 Дневник благодарности"],
        ["🎵 Музыка для релакса", "↩️ Назад"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Inline клавиатура настроек"""
    keyboard = [
        [
            InlineKeyboardButton("🔔 Уведомления", callback_data="settings_notifications"),
            InlineKeyboardButton("🌙 Темная тема", callback_data="settings_theme")
        ],
        [
            InlineKeyboardButton("🗑️ Очистить историю", callback_data="settings_clear"),
            InlineKeyboardButton("📊 Экспорт данных", callback_data="settings_export")
        ],
        [
            InlineKeyboardButton("❓ Помощь", callback_data="settings_help"),
            InlineKeyboardButton("↩️ Назад", callback_data="settings_back")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_ai_chat_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для чата с ИИ"""
    keyboard = [
        ["🔄 Новый диалог", "💭 Примеры вопросов"],
        ["📋 История диалогов", "↩️ Выйти из чата"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_crisis_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для кризисной ситуации"""
    keyboard = [
        ["📞 Телефон доверия", "🏥 Вызов скорой"],
        ["💬 Поговорить с ИИ", "👨‍⚕️ Найти психолога"],
        ["↩️ Вернуться в меню"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Да", callback_data="confirm_yes"),
            InlineKeyboardButton("❌ Нет", callback_data="confirm_no")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_stats_period_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора периода статистики"""
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

# Утилиты для создания кнопок
def create_contact_button() -> KeyboardButton:
    """Создать кнопку для отправки контакта"""
    return KeyboardButton(text="📱 Отправить контакт", request_contact=True)

def create_location_button() -> KeyboardButton:
    """Создать кнопку для отправки местоположения"""
    return KeyboardButton(text="📍 Отправить местоположение", request_location=True)

# Экспортируем все клавиатуры
__all__ = [
    'get_main_keyboard',
    'get_mood_keyboard',
    'get_exercises_keyboard',
    'get_settings_keyboard',
    'get_ai_chat_keyboard',
    'get_crisis_keyboard',
    'get_confirmation_keyboard',
    'get_stats_period_keyboard',
    'create_contact_button',
    'create_location_button'
]
