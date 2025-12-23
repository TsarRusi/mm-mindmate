import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import asyncio
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Для работы без GUI
import pandas as pd
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

def format_date(date_str: str) -> str:
    """Форматирование даты для отображения."""
    if not date_str:
        return "Нет даты"
    
    try:
        if isinstance(date_str, str):
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            dt = date_str
        
        # Для сегодня/вчера
        today = datetime.now().date()
        dt_date = dt.date() if isinstance(dt, datetime) else dt
        
        if dt_date == today:
            return "Сегодня"
        elif dt_date == today - timedelta(days=1):
            return "Вчера"
        elif dt_date == today - timedelta(days=2):
            return "Позавчера"
        elif dt_date.year == today.year:
            return dt.strftime("%d.%m")
        else:
            return dt.strftime("%d.%m.%Y")
            
    except Exception as e:
        logger.error(f"Ошибка форматирования даты {date_str}: {e}")
        return str(date_str)[:10]

def generate_mood_chart(user_id: int, days: int = 30) -> Optional[BytesIO]:
    """Генерация графика настроения."""
    try:
        # Здесь должна быть логика получения данных из БД
        # Заглушка для примера
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        moods = np.random.randint(3, 9, size=days) + np.random.randn(days) * 0.5
        moods = np.clip(moods, 1, 10)
        
        # Создаем график
        plt.figure(figsize=(10, 6))
        plt.plot(dates, moods, marker='o', linewidth=2, markersize=6, color='#4A90E2')
        plt.fill_between(dates, moods, alpha=0.3, color='#4A90E2')
        
        # Настройки графика
        plt.title('Настроение за последние 30 дней', fontsize=16, pad=20)
        plt.xlabel('Дата', fontsize=12)
        plt.ylabel('Настроение (1-10)', fontsize=12)
        plt.ylim(0, 11)
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Сохраняем в BytesIO
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        plt.close()
        
        return buf
        
    except Exception as e:
        logger.error(f"Ошибка генерации графика: {e}")
        return None

def calculate_streak(dates: List[datetime]) -> int:
    """Расчет серии дней подряд."""
    if not dates:
        return 0
    
    sorted_dates = sorted(set(dates), reverse=True)
    streak = 0
    current_date = datetime.now().date()
    
    for date in sorted_dates:
        date_date = date.date() if isinstance(date, datetime) else date
        if date_date == current_date - timedelta(days=streak):
            streak += 1
        else:
            break
    
    return streak

def validate_mood_score(score: int) -> bool:
    """Проверка валидности оценки настроения."""
    return 1 <= score <= 10

def truncate_text(text: str, max_length: int = 100) -> str:
    """Обрезать текст до максимальной длины."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def format_time_ago(dt: datetime) -> str:
    """Форматирование времени в формате "сколько времени назад"."""
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} год{'' if years == 1 else 'а' if 2 <= years <= 4 else 'ов'} назад"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} месяц{'' if months == 1 else 'а' if 2 <= months <= 4 else 'ев'} назад"
    elif diff.days > 0:
        return f"{diff.days} д{'' if diff.days == 1 else 'ня' if 2 <= diff.days <= 4 else 'ней'} назад"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} час{'' if hours == 1 else 'а' if 2 <= hours <= 4 else 'ов'} назад"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} минут{'' if minutes == 1 else 'ы' if 2 <= minutes <= 4 else ''} назад"
    else:
        return "только что"

def parse_time_string(time_str: str) -> Optional[Tuple[int, int]]:
    """Парсинг строки времени HH:MM."""
    try:
        if ':' in time_str:
            hours, minutes = map(int, time_str.split(':'))
            if 0 <= hours <= 23 and 0 <= minutes <= 59:
                return hours, minutes
        return None
    except:
        return None

def escape_markdown(text: str) -> str:
    """Экранирование символов Markdown для Telegram."""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text

def create_progress_bar(value: float, max_value: float = 10, length: int = 10) -> str:
    """Создание текстового прогресс-бара."""
    filled = int(round(value / max_value * length))
    empty = length - filled
    return '█' * filled + '░' * empty

async def rate_limit_check(user_id: int, action: str, 
                          limit_per_hour: int = 10) -> bool:
    """Проверка лимита запросов."""
    # Здесь должна быть реализация проверки лимитов
    # Например, с использованием Redis или БД
    return True  # Заглушка

def format_number(num: float) -> str:
    """Форматирование чисел для отображения."""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    elif num.is_integer():
        return str(int(num))
    else:
        return f"{num:.2f}"

def sanitize_user_input(text: str, max_length: int = 2000) -> str:
    """Очистка пользовательского ввода."""
    # Обрезаем длину
    text = text[:max_length]
    
    # Удаляем опасные символы (базовая защита)
    dangerous = ['<script>', 'javascript:', 'onload=', 'onerror=']
    for danger in dangerous:
        text = text.replace(danger, '')
    
    # Удаляем множественные переносы строк
    text = '\n'.join([line.strip() for line in text.split('\n') if line.strip()])
    
    return text.strip()

class RateLimiter:
    """Простой rate limiter."""
    
    def __init__(self, max_requests: int = 10, period: int = 3600):
        self.max_requests = max_requests
        self.period = period
        self.requests = {}
    
    def check(self, user_id: int) -> bool:
        """Проверить, можно ли выполнить запрос."""
        now = datetime.now()
        user_requests = self.requests.get(user_id, [])
        
        # Удаляем старые запросы
        user_requests = [req_time for req_time in user_requests 
                        if (now - req_time).seconds < self.period]
        
        if len(user_requests) >= self.max_requests:
            return False
        
        user_requests.append(now)
        self.requests[user_id] = user_requests
        return True
    
    def get_wait_time(self, user_id: int) -> int:
        """Получить время ожидания в секундах."""
        user_requests = self.requests.get(user_id, [])
        if not user_requests:
            return 0
        
        oldest = min(user_requests)
        wait_until = oldest + timedelta(seconds=self.period)
        wait_seconds = max(0, (wait_until - datetime.now()).seconds)
        return wait_seconds