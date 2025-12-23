from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, JSON, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import json
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from config import settings

# Создаем движок БД
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency для FastAPI (если будет веб-интерфейс)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def session_scope():
    """Контекстный менеджер для сессий БД."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

class User(Base):
    """Модель пользователя."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    language_code = Column(String(10), default="ru")
    
    # Настройки пользователя
    daily_reminder_enabled = Column(Boolean, default=True)
    reminder_time = Column(String(5), default="19:00")  # HH:MM
    theme = Column(String(20), default="light")  # light/dark
    
    # Статистика
    total_messages = Column(Integer, default=0)
    total_sessions = Column(Integer, default=0)
    subscription_tier = Column(String(20), default="free")  # free/premium
    
    # Безопасность
    is_active = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False)
    ban_reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "telegram_id": self.telegram_id,
            "username": self.username,
            "first_name": self.first_name,
            "total_messages": self.total_messages,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_active": self.last_active.isoformat() if self.last_active else None
        }

class MoodLog(Base):
    """Запись настроения пользователя."""
    __tablename__ = "mood_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    
    # Оценки
    mood_score = Column(Integer)  # 1-10
    anxiety_score = Column(Integer)  # 1-10
    energy_score = Column(Integer)  # 1-10
    
    # Текст и анализ
    user_message = Column(Text)
    ai_analysis = Column(JSON)  # Результат NLP анализа
    
    # Теги и категории
    tags = Column(JSON)  # Список тегов
    category = Column(String(50))  # работа/семья/здоровье...
    
    # Метаданные
    session_id = Column(String(50))  # ID сессии
    message_type = Column(String(20))  # mood/chat/exercise...
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "mood_score": self.mood_score,
            "user_message": self.user_message,
            "ai_analysis": self.ai_analysis,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class ChatSession(Base):
    """Сессия чата с DeepSeek AI."""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    session_uuid = Column(String(36), unique=True, index=True)
    
    # Контекст
    system_prompt = Column(Text)
    context_messages = Column(JSON)  # История сообщений
    
    # Статистика
    message_count = Column(Integer, default=0)
    token_count = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    
    # Состояние
    is_active = Column(Boolean, default=True)
    last_message_at = Column(DateTime, default=datetime.utcnow)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    
    @property
    def duration(self) -> Optional[float]:
        if self.ended_at and self.created_at:
            return (self.ended_at - self.created_at).total_seconds()
        return None

class Exercise(Base):
    """Психологические упражнения."""
    __tablename__ = "exercises"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50))  # breathing/mindfulness/cbt...
    difficulty = Column(String(20))  # easy/medium/hard
    duration_minutes = Column(Integer)
    
    # Описание
    title = Column(String(200))
    description = Column(Text)
    instructions = Column(JSON)  # Пошаговые инструкции
    tips = Column(JSON)  # Советы
    
    # Метаданные
    tags = Column(JSON)
    language = Column(String(10), default="ru")
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DatabaseManager:
    """Менеджер для работы с БД."""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
        
    def init_db(self):
        """Инициализация базы данных."""
        Base.metadata.create_all(bind=self.engine)
    
    def get_user(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID."""
        with session_scope() as session:
            return session.query(User).filter(User.telegram_id == telegram_id).first()
    
    def create_user(self, telegram_id: int, username: str = None, 
                   first_name: str = None, last_name: str = None) -> User:
        """Создать нового пользователя."""
        with session_scope() as session:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            session.add(user)
            session.flush()
            return user
    
    def get_or_create_user(self, telegram_id: int, **kwargs) -> User:
        """Получить или создать пользователя."""
        user = self.get_user(telegram_id)
        if not user:
            user = self.create_user(telegram_id, **kwargs)
        return user
    
    def add_mood_log(self, user_id: int, **kwargs) -> MoodLog:
        """Добавить запись настроения."""
        with session_scope() as session:
            mood_log = MoodLog(user_id=user_id, **kwargs)
            session.add(mood_log)
            
            # Обновляем статистику пользователя
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                user.total_messages += 1
                user.last_active = datetime.utcnow()
            
            session.flush()
            return mood_log
    
    def get_user_mood_stats(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Получить статистику настроения пользователя."""
        with session_scope() as session:
            from_date = datetime.utcnow() - timedelta(days=days)
            
            # Среднее настроение
            avg_mood = session.query(func.avg(MoodLog.mood_score))\
                .filter(MoodLog.user_id == user_id, MoodLog.created_at >= from_date)\
                .scalar()
            
            # Количество записей
            count = session.query(func.count(MoodLog.id))\
                .filter(MoodLog.user_id == user_id, MoodLog.created_at >= from_date)\
                .scalar()
            
            # Последние записи
            recent = session.query(MoodLog)\
                .filter(MoodLog.user_id == user_id)\
                .order_by(MoodLog.created_at.desc())\
                .limit(10)\
                .all()
            
            return {
                "avg_mood": float(avg_mood) if avg_mood else None,
                "total_records": count,
                "recent_logs": [log.to_dict() for log in recent]
            }

# Создаем менеджер БД
db_manager = DatabaseManager()