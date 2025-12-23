import logging
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Pydantic модели для валидации
class UserBase(BaseModel):
    """Базовая модель пользователя"""
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None

class UserCreate(UserBase):
    """Модель для создания пользователя"""
    pass

class UserResponse(UserBase):
    """Модель ответа с пользователем"""
    id: int
    created_at: datetime
    last_active: datetime
    
    class Config:
        from_attributes = True

class MoodLogBase(BaseModel):
    """Базовая модель записи настроения"""
    user_id: int
    mood_score: Optional[int] = Field(None, ge=1, le=10)
    user_message: Optional[str] = None

class MoodLogCreate(MoodLogBase):
    """Модель для создания записи настроения"""
    pass

class MoodLogResponse(MoodLogBase):
    """Модель ответа с записью настроения"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChatHistoryBase(BaseModel):
    """Базовая модель истории чата"""
    user_id: int
    user_message: str
    ai_response: str
    message_type: str = "text"

class ChatHistoryCreate(ChatHistoryBase):
    """Модель для создания истории чата"""
    pass

class ChatHistoryResponse(ChatHistoryBase):
    """Модель ответа с историей чата"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Статистика
class UserStats(BaseModel):
    """Статистика пользователя"""
    total_records: int
    avg_mood: Optional[float]
    recent_logs: List[dict]
    
class DailyStats(BaseModel):
    """Дневная статистика"""
    date: str
    avg_mood: float
    message_count: int

# Для ответов API
class APIResponse(BaseModel):
    """Базовый ответ API"""
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None

# Экспортируем все модели
__all__ = [
    'UserBase', 'UserCreate', 'UserResponse',
    'MoodLogBase', 'MoodLogCreate', 'MoodLogResponse',
    'ChatHistoryBase', 'ChatHistoryCreate', 'ChatHistoryResponse',
    'UserStats', 'DailyStats', 'APIResponse'
]
