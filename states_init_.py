"""
Модуль состояний для FSM (Finite State Machine)
"""

from states.user_states import (
    UserStates,
    ConversationState,
    get_state_name,
    set_user_state,
    get_user_state,
    clear_user_state
)

__all__ = [
    'UserStates',
    'ConversationState',
    'get_state_name',
    'set_user_state', 
    'get_user_state',
    'clear_user_state'
]
