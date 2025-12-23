import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def format_datetime(dt: datetime) -> str:
    """Форматирование даты-времени"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def get_time_ago(dt: datetime) -> str:
    """Время назад в читаемом формате"""
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} год назад" if years == 1 else f"{years} лет назад"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} месяц назад" if months == 1 else f"{months} месяцев назад"
    elif diff.days > 0:
        return f"{diff.days} дней назад"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} час назад" if hours == 1 else f"{hours} часов назад"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} минут назад"
    else:
        return "только что"

def validate_mood_score(score: Any) -> Optional[int]:
    """Проверка корректности оценки настроения"""
    try:
        score_int = int(score)
        if 1 <= score_int <= 10:
            return score_int
    except (ValueError, TypeError):
        pass
    return None

def truncate_text(text: str, max_length: int = 100) -> str:
    """Обрезать текст до максимальной длины"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def get_mood_emoji(score: int) -> str:
    """Получить эмодзи для оценки настроения"""
    if score >= 9:
        return "😍"
    elif score >= 8:
        return "😊"
    elif score >= 7:
        return "🙂"
    elif score >= 5:
        return "😐"
    elif score >= 4:
        return "😕"
    elif score >= 3:
        return "😔"
    elif score >= 2:
        return "😢"
    else:
        return "😭"

def create_keyboard(buttons: list, columns: int = 2) -> list:
    """Создать клавиатуру из кнопок"""
    keyboard = []
    row = []
    
    for i, button in enumerate(buttons):
        row.append(button)
        if (i + 1) % columns == 0:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    return keyboard

def safe_get(data: Dict, keys: str, default: Any = None) -> Any:
    """Безопасное получение значения из словаря"""
    keys_list = keys.split('.')
    current = data
    
    for key in keys_list:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current

class RateLimiter:
    """Ограничитель запросов"""
    
    def __init__(self, max_requests: int = 5, period_seconds: int = 60):
        self.max_requests = max_requests
        self.period = period_seconds
        self.requests = {}
    
    def check_limit(self, user_id: int) -> bool:
        """Проверить лимит для пользователя"""
        now = datetime.utcnow()
        
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        # Удаляем старые запросы
        cutoff = now - timedelta(seconds=self.period)
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if req_time > cutoff
        ]
        
        # Проверяем лимит
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        
        # Добавляем текущий запрос
        self.requests[user_id].append(now)
        return True
    
    def get_remaining(self, user_id: int) -> int:
        """Получить оставшееся количество запросов"""
        now = datetime.utcnow()
        
        if user_id not in self.requests:
            return self.max_requests
        
        cutoff = now - timedelta(seconds=self.period)
        valid_requests = [
            req_time for req_time in self.requests[user_id]
            if req_time > cutoff
        ]
        
        return max(0, self.max_requests - len(valid_requests))
