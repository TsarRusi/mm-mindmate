from enum import Enum

class UserStates(Enum):
    """Состояния пользователя."""
    MAIN_MENU = "main_menu"
    MOOD_INPUT = "mood_input"
    AI_CHAT = "ai_chat"
    EXERCISE = "exercise"
    SETTINGS = "settings"
    STATS = "stats"
    CRISIS_HELP = "crisis_help"