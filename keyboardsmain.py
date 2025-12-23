from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional

def get_main_menu() -> ReplyKeyboardMarkup:
    """Главное меню."""
    keyboard = [
        ["📊 Записать настроение", "💬 Поговорить с ИИ"],
        ["🧘 Упражнения", "📈 Статистика"],
        ["⚙️ Настройки", "❓ Помощь"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_ai_chat_menu() -> InlineKeyboardMarkup:
    """Меню для чата с ИИ."""
    keyboard = [
        [
            InlineKeyboardButton("🧠 Психолог", callback_data="ai_mode_psychologist"),
            InlineKeyboardButton("🎯 Коуч", callback_data="ai_mode_coach")
        ],
        [
            InlineKeyboardButton("👥 Друг", callback_data="ai_mode_friend"),
            InlineKeyboardButton("❌ Закрыть чат", callback_data="ai_end_session")
        ],
        [
            InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_mood_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для оценки настроения."""
    keyboard = []
    
    # Первый ряд: 1-5
    row1 = []
    for i in range(1, 6):
        emoji = "😢" if i == 1 else "😔" if i <= 3 else "😐" if i == 4 else "🙂"
        row1.append(InlineKeyboardButton(f"{emoji} {i}", callback_data=f"mood_{i}"))
    
    # Второй ряд: 6-10
    row2 = []
    for i in range(6, 11):
        emoji = "😊" if i <= 7 else "😄" if i <= 9 else "🤩"
        row2.append(InlineKeyboardButton(f"{emoji} {i}", callback_data=f"mood_{i}"))
    
    keyboard.append(row1)
    keyboard.append(row2)
    keyboard.append([InlineKeyboardButton("✍️ Описать текстом", callback_data="mood_text")])
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(keyboard)

def get_exercises_menu() -> InlineKeyboardMarkup:
    """Меню упражнений."""
    keyboard = [
        [
            InlineKeyboardButton("🌬️ Дыхание", callback_data="exercise_breathing"),
            InlineKeyboardButton("🧠 Осознанность", callback_data="exercise_mindfulness")
        ],
        [
            InlineKeyboardButton("💭 КПТ техники", callback_data="exercise_cbt"),
            InlineKeyboardButton("📝 Дневник", callback_data="exercise_journal")
        ],
        [
            InlineKeyboardButton("🎵 Медитация", callback_data="exercise_meditation"),
            InlineKeyboardButton("🏃 Тело", callback_data="exercise_body")
        ],
        [
            InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_settings_menu() -> InlineKeyboardMarkup:
    """Меню настроек."""
    keyboard = [
        [
            InlineKeyboardButton("🔔 Напоминания", callback_data="settings_reminders"),
            InlineKeyboardButton("🌙 Тема", callback_data="settings_theme")
        ],
        [
            InlineKeyboardButton("🗣️ Язык", callback_data="settings_language"),
            InlineKeyboardButton("📊 Данные", callback_data="settings_data")
        ],
        [
            InlineKeyboardButton("👤 Профиль", callback_data="settings_profile"),
            InlineKeyboardButton("🛡️ Безопасность", callback_data="settings_security")
        ],
        [
            InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_statistics_menu() -> InlineKeyboardMarkup:
    """Меню статистики."""
    keyboard = [
        [
            InlineKeyboardButton("📅 За неделю", callback_data="stats_week"),
            InlineKeyboardButton("📆 За месяц", callback_data="stats_month")
        ],
        [
            InlineKeyboardButton("📊 Все время", callback_data="stats_all"),
            InlineKeyboardButton("📈 Графики", callback_data="stats_charts")
        ],
        [
            InlineKeyboardButton("🏷️ По тегам", callback_data="stats_tags"),
            InlineKeyboardButton("🔄 Тренды", callback_data="stats_trends")
        ],
        [
            InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_crisis_help_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для кризисной помощи."""
    keyboard = [
        [
            InlineKeyboardButton("📞 Телефоны доверия", callback_data="crisis_phones"),
            InlineKeyboardButton("🌐 Онлайн помощь", callback_data="crisis_online")
        ],
        [
            InlineKeyboardButton("🚨 Экстренные службы", callback_data="crisis_emergency"),
            InlineKeyboardButton("🏥 Найти психолога", callback_data="crisis_find_help")
        ],
        [
            InlineKeyboardButton("💬 Поговорить с ИИ", callback_data="ai_mode_psychologist"),
            InlineKeyboardButton("🧘 Успокоиться", callback_data="exercise_breathing")
        ],
        [
            InlineKeyboardButton("✅ Я в порядке", callback_data="crisis_ok")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_confirmation_keyboard(yes_data: str, no_data: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Да", callback_data=yes_data),
            InlineKeyboardButton("❌ Нет", callback_data=no_data)
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard(back_data: str = "back_to_main") -> InlineKeyboardMarkup:
    """Простая кнопка назад."""
    keyboard = [
        [InlineKeyboardButton("⬅️ Назад", callback_data=back_data)]
    ]
    return InlineKeyboardMarkup(keyboard)