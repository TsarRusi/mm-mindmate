import logging
from enum import Enum
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class UserStates(Enum):
    """Состояния пользователя в FSM"""
    MAIN_MENU = "main_menu"
    WAITING_FOR_MOOD = "waiting_for_mood"
    WAITING_FOR_MOOD_TEXT = "waiting_for_mood_text"
    IN_AI_CHAT = "in_ai_chat"
    WAITING_FOR_EXERCISE_CHOICE = "waiting_for_exercise_choice"
    WAITING_FOR_SETTINGS_CHOICE = "waiting_for_settings_choice"
    IN_CRISIS_MODE = "in_crisis_mode"
    WAITING_FOR_FEEDBACK = "waiting_for_feedback"
    WAITING_FOR_STATS_PERIOD = "waiting_for_stats_period"
    WAITING_FOR_CONFIRMATION = "waiting_for_confirmation"

class ConversationState:
    """Класс для управления состоянием диалога"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.state = UserStates.MAIN_MENU
        self.context = {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def update_state(self, new_state: UserStates):
        """Обновить состояние"""
        self.state = new_state
        self.updated_at = datetime.utcnow()
        logger.debug(f"Пользователь {self.user_id}: состояние изменено на {new_state}")
    
    def update_context(self, key: str, value: any):
        """Обновить контекст"""
        self.context[key] = value
        self.updated_at = datetime.utcnow()
    
    def get_context(self, key: str, default=None):
        """Получить значение из контекста"""
        return self.context.get(key, default)
    
    def clear_context(self):
        """Очистить контекст"""
        self.context = {}
        logger.debug(f"Контекст пользователя {self.user_id} очищен")
    
    def to_dict(self) -> Dict:
        """Преобразовать в словарь"""
        return {
            'user_id': self.user_id,
            'state': self.state.value,
            'context': self.context,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Создать из словаря"""
        state = cls(data['user_id'])
        state.state = UserStates(data['state'])
        state.context = data.get('context', {})
        state.created_at = datetime.fromisoformat(data['created_at'])
        state.updated_at = datetime.fromisoformat(data['updated_at'])
        return state

# Глобальное хранилище состояний (в продакшене использовать Redis/БД)
_user_states: Dict[int, ConversationState] = {}

def set_user_state(user_id: int, state: UserStates, context: Optional[Dict] = None):
    """Установить состояние пользователя"""
    if user_id not in _user_states:
        _user_states[user_id] = ConversationState(user_id)
    
    _user_states[user_id].update_state(state)
    
    if context:
        for key, value in context.items():
            _user_states[user_id].update_context(key, value)
    
    logger.debug(f"Состояние пользователя {user_id} установлено: {state.value}")

def get_user_state(user_id: int) -> Optional[ConversationState]:
    """Получить состояние пользователя"""
    return _user_states.get(user_id)

def clear_user_state(user_id: int):
    """Очистить состояние пользователя"""
    if user_id in _user_states:
        del _user_states[user_id]
        logger.debug(f"Состояние пользователя {user_id} очищено")

def get_state_name(state: UserStates) -> str:
    """Получить читаемое имя состояния"""
    names = {
        UserStates.MAIN_MENU: "Главное меню",
        UserStates.WAITING_FOR_MOOD: "Ожидание оценки настроения",
        UserStates.WAITING_FOR_MOOD_TEXT: "Ожидание описания настроения",
        UserStates.IN_AI_CHAT: "Чат с ИИ",
        UserStates.WAITING_FOR_EXERCISE_CHOICE: "Выбор упражнения",
        UserStates.WAITING_FOR_SETTINGS_CHOICE: "Настройки",
        UserStates.IN_CRISIS_MODE: "Кризисный режим",
        UserStates.WAITING_FOR_FEEDBACK: "Ожидание отзыва",
        UserStates.WAITING_FOR_STATS_PERIOD: "Выбор периода статистики",
        UserStates.WAITING_FOR_CONFIRMATION: "Ожидание подтверждения"
    }
    return names.get(state, "Неизвестное состояние")

def get_all_states() -> Dict[int, Dict]:
    """Получить все состояния (для админки)"""
    return {
        user_id: state.to_dict()
        for user_id, state in _user_states.items()
    }

def cleanup_old_states(hours: int = 24):
    """Очистить старые состояния"""
    now = datetime.utcnow()
    to_remove = []
    
    for user_id, state in _user_states.items():
        age_hours = (now - state.updated_at).total_seconds() / 3600
        if age_hours > hours:
            to_remove.append(user_id)
    
    for user_id in to_remove:
        del _user_states[user_id]
    
    if to_remove:
        logger.info(f"Очищено {len(to_remove)} старых состояний")

# Экспортируем всё
__all__ = [
    'UserStates',
    'ConversationState',
    'set_user_state',
    'get_user_state',
    'clear_user_state',
    'get_state_name',
    'get_all_states',
    'cleanup_old_states'
]
