"""
Клавиатуры для MindMate Bot
Красивое оформление с эмодзи
"""

from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard():
    """Основная клавиатура меню"""
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

def get_stats_keyboard():
    """Клавиатура статистики"""
    keyboard = [
        ["📅 Сегодня", "📆 Неделя"],
        ["🗓️ Месяц", "📊 Все время"],
        ["↩️ Назад в меню"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_settings_keyboard():
    """Клавиатура настроек"""
    keyboard = [
        ["🔔 Уведомления", "🌙 Тема"],
        ["🔒 Конфиденциальность", "💾 Автосохранение"],
        ["↩️ Назад в меню"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_help_keyboard():
    """Клавиатура помощи"""
    keyboard = [
        ["📞 Контакты", "📚 Инструкция"],
        ["🆘 Экстренная помощь", "💡 Советы"],
        ["↩️ Назад в меню"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_crisis_keyboard():
    """Клавиатура экстренной помощи"""
    keyboard = [
        ["📞 Телефон доверия", "🏥 Вызов скорой"],
        ["💬 Поддержка онлайн", "👥 Близкие люди"],
        ["↩️ Назад в меню"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_ai_chat_keyboard():
    """Клавиатура чата с ИИ"""
    keyboard = [
        ["🔄 Новый диалог", "💭 Примеры вопросов"],
        ["📋 История", "🎯 Рекомендации"],
        ["↩️ Выйти из чата"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_back_keyboard():
    """Простая кнопка назад"""
    keyboard = [["↩️ Назад в меню"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Inline клавиатуры для статистики
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
        ],
        [
            InlineKeyboardButton("📈 График", callback_data="stats_graph"),
            InlineKeyboardButton("📋 Отчет", callback_data="stats_report")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_settings_inline_keyboard():
    """Inline клавиатура настроек"""
    keyboard = [
        [
            InlineKeyboardButton("🔔 Уведомления", callback_data="settings_notifications"),
            InlineKeyboardButton("🌙 Темная тема", callback_data="settings_dark_theme")
        ],
        [
            InlineKeyboardButton("🔒 Приватность", callback_data="settings_privacy"),
            InlineKeyboardButton("💾 Автосохранение", callback_data="settings_autosave")
        ],
        [
            InlineKeyboardButton("🗑️ Очистить историю", callback_data="settings_clear"),
            InlineKeyboardButton("📤 Экспорт данных", callback_data="settings_export")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_confirmation_inline_keyboard():
    """Inline клавиатура подтверждения"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Да", callback_data="confirm_yes"),
            InlineKeyboardButton("❌ Нет", callback_data="confirm_no")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Экспорт всех клавиатур
__all__ = [
    'get_main_keyboard',
    'get_mood_keyboard',
    'get_exercises_keyboard',
    'get_stats_keyboard',
    'get_settings_keyboard',
    'get_help_keyboard',
    'get_crisis_keyboard',
    'get_ai_chat_keyboard',
    'get_back_keyboard',
    'get_stats_inline_keyboard',
    'get_settings_inline_keyboard',
    'get_confirmation_inline_keyboard'
]
