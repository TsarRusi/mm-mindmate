import os
import logging
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Получаем DATABASE_URL из переменных окружения Render
DATABASE_URL = os.environ.get('DATABASE_URL')

# Для локальной разработки
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///mindmate.db"
    logger.info("Используется SQLite для локальной разработки")

# Исправляем URL для SQLAlchemy (Render использует postgres://, нужно postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    logger.info("URL базы данных исправлен для SQLAlchemy")

try:
    # Создаем движок с настройками для Render
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False  # В продакшене выключить
    )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    
    logger.info(f"✅ Движок БД создан: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else 'SQLite'}")
    
except Exception as e:
    logger.error(f"❌ Ошибка создания движка БД: {e}")
    # Создаем fallback для SQLite если PostgreSQL не работает
    DATABASE_URL = "sqlite:///mindmate.db"
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    logger.info("✅ Используем SQLite как fallback")

@contextmanager
def get_db_session():
    """Контекстный менеджер для сессий БД"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка БД: {e}")
        raise
    finally:
        session.close()

class User(Base):
    """Модель пользователя (упрощенная)"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String(100))
    first_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

class MoodLog(Base):
    """Записи настроения (упрощенная)"""
    __tablename__ = "mood_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    mood_score = Column(Integer)
    user_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class DatabaseManager:
    """Менеджер для работы с БД на Render"""
    
    def __init__(self):
        self.engine = engine
        self.Base = Base
        
    def init_db(self):
        """Инициализация таблиц"""
        try:
            self.Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Таблицы БД созданы/проверены")
        except Exception as e:
            logger.error(f"❌ Ошибка создания таблиц: {e}")
    
    def add_user(self, telegram_id, username=None, first_name=None):
        """Добавить пользователя"""
        with get_db_session() as session:
            # Проверяем существование
            existing = session.query(User).filter(User.telegram_id == telegram_id).first()
            if existing:
                existing.last_active = datetime.utcnow()
                session.commit()
                return existing
            
            # Создаем нового
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name
            )
            session.add(user)
            session.commit()
            return user
    
    def add_mood_log(self, user_id, mood_score=None, message=None):
        """Добавить запись настроения"""
        with get_db_session() as session:
            log = MoodLog(
                user_id=user_id,
                mood_score=mood_score,
                user_message=message
            )
            session.add(log)
            session.commit()
            return log
    
    def get_user_stats(self, user_id):
        """Получить статистику пользователя"""
        with get_db_session() as session:
            # Количество записей
            count = session.query(MoodLog).filter(MoodLog.user_id == user_id).count()
            
            # Среднее настроение
            from sqlalchemy import func
            avg_mood = session.query(func.avg(MoodLog.mood_score)) \
                .filter(MoodLog.user_id == user_id) \
                .filter(MoodLog.mood_score.isnot(None)) \
                .scalar()
            
            # Последние записи
            recent = session.query(MoodLog) \
                .filter(MoodLog.user_id == user_id) \
                .order_by(MoodLog.created_at.desc()) \
                .limit(5) \
                .all()
            
            return {
                "total_records": count,
                "avg_mood": float(avg_mood) if avg_mood else None,
                "recent_logs": [
                    {
                        "mood_score": log.mood_score,
                        "message": log.user_message[:50] + "..." if log.user_message and len(log.user_message) > 50 else log.user_message,
                        "created_at": log.created_at.isoformat() if log.created_at else None
                    }
                    for log in recent
                ]
            }

# Создаем глобальный экземпляр менеджера БД
db_manager = DatabaseManager()
