"""
Файл для работы с базой данных
Безопасная версия для Render - не ломает бот при отсутствии DATABASE_URL
"""

import os
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# ============ ПРОВЕРКА DATABASE_URL С ЗАЩИТОЙ ============
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    logger.warning("⚠️ DATABASE_URL не найден! Будет использован режим без БД.")
    USE_REAL_DB = False
else:
    logger.info(f"✅ DATABASE_URL найден: {DATABASE_URL[:50]}...")
    USE_REAL_DB = True

# ============ РЕЖИМ БЕЗ БАЗЫ ДАННЫХ (ЗАГЛУШКА) ============
if not USE_REAL_DB:
    logger.info("🔧 Используется заглушка базы данных")
    
    class DummySession:
        def query(self, *args, **kwargs):
            return self
        def filter(self, *args, **kwargs):
            return self
        def first(self):
            return None
        def all(self):
            return []
        def count(self):
            return 0
        def commit(self):
            pass
        def rollback(self):
            pass
        def close(self):
            pass
    
    class DummyDBManager:
        """Заглушка для работы без реальной базы данных"""
        def init_db(self):
            logger.info("✅ Заглушка БД инициализирована")
            return True
        
        def add_user(self, telegram_id, username=None, first_name=None):
            logger.info(f"📝 Пользователь добавлен (заглушка): ID={telegram_id}, Имя={first_name}")
            return {"id": telegram_id, "telegram_id": telegram_id}
        
        def add_mood_log(self, user_id, mood_score=None, message=None):
            logger.info(f"📊 Запись настроения (заглушка): user={user_id}, score={mood_score}")
            return {"id": 1, "user_id": user_id}
        
        def get_user_stats(self, user_id):
            return {
                "total_records": 0,
                "avg_mood": None,
                "recent_logs": []
            }
        
        @contextmanager
        def get_db_session(self):
            """Контекстный менеджер для сессий-заглушек"""
            session = DummySession()
            try:
                yield session
                session.commit()
            except Exception as e:
                session.rollback()
                logger.error(f"Ошибка в заглушке БД: {e}")
            finally:
                session.close()
    
    db_manager = DummyDBManager()

# ============ РЕЖИМ С РЕАЛЬНОЙ БАЗОЙ ДАННЫХ ============
else:
    try:
        # Импортируем SQLAlchemy только если нужна реальная БД
        from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, func
        from sqlalchemy.ext.declarative import declarative_base
        from sqlalchemy.orm import sessionmaker
        from datetime import datetime
        
        # Исправляем URL для SQLAlchemy
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
            logger.info("✅ URL базы данных исправлен для SQLAlchemy")
        
        # Создаем движок
        engine = create_engine(
            DATABASE_URL,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False
        )
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base = declarative_base()
        
        logger.info("✅ Движок PostgreSQL создан")
        
        # ============ МОДЕЛИ ============
        
        class User(Base):
            __tablename__ = "users"
            
            id = Column(Integer, primary_key=True, index=True)
            telegram_id = Column(Integer, unique=True, index=True, nullable=False)
            username = Column(String(100))
            first_name = Column(String(100))
            created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
            last_active = Column(DateTime, default=datetime.utcnow, nullable=False)
        
        class MoodLog(Base):
            __tablename__ = "mood_logs"
            
            id = Column(Integer, primary_key=True, index=True)
            user_id = Column(Integer, index=True, nullable=False)
            mood_score = Column(Integer)
            user_message = Column(Text)
            created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
        
        # ============ МЕНЕДЖЕР БАЗЫ ДАННЫХ ============
        
        class DatabaseManager:
            def __init__(self):
                self.engine = engine
                self.Base = Base
            
            def init_db(self):
                """Создание таблиц с защитой от ошибок"""
                try:
                    self.Base.metadata.create_all(bind=self.engine)
                    logger.info("✅ Таблицы БД созданы/проверены")
                    return True
                except Exception as e:
                    logger.error(f"❌ Ошибка создания таблиц: {e}")
                    # Пробуем создать через raw SQL
                    try:
                        with self.engine.connect() as conn:
                            # Создаем таблицу users
                            conn.execute("""
                                CREATE TABLE IF NOT EXISTS users (
                                    id SERIAL PRIMARY KEY,
                                    telegram_id INTEGER UNIQUE NOT NULL,
                                    username VARCHAR(100),
                                    first_name VARCHAR(100),
                                    created_at TIMESTAMP DEFAULT NOW(),
                                    last_active TIMESTAMP DEFAULT NOW()
                                )
                            """)
                            # Создаем таблицу mood_logs
                            conn.execute("""
                                CREATE TABLE IF NOT EXISTS mood_logs (
                                    id SERIAL PRIMARY KEY,
                                    user_id INTEGER NOT NULL,
                                    mood_score INTEGER,
                                    user_message TEXT,
                                    created_at TIMESTAMP DEFAULT NOW()
                                )
                            """)
                            conn.commit()
                        logger.info("✅ Таблицы созданы через raw SQL")
                        return True
                    except Exception as e2:
                        logger.error(f"❌ Ошибка создания таблиц raw SQL: {e2}")
                        return False
            
            @contextmanager
            def get_db_session(self):
                """Контекстный менеджер для сессий"""
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
            
            def add_user(self, telegram_id, username=None, first_name=None):
                """Добавить пользователя"""
                try:
                    with self.get_db_session() as session:
                        # Проверяем существование
                        existing = session.query(User).filter(
                            User.telegram_id == telegram_id
                        ).first()
                        
                        if existing:
                            existing.last_active = datetime.utcnow()
                            session.commit()
                            logger.info(f"👤 Пользователь обновлен: {telegram_id}")
                            return {"id": existing.id, "telegram_id": existing.telegram_id}
                        
                        # Создаем нового
                        user = User(
                            telegram_id=telegram_id,
                            username=username,
                            first_name=first_name
                        )
                        session.add(user)
                        session.commit()
                        session.refresh(user)
                        
                        logger.info(f"👤 Новый пользователь: {telegram_id} ({first_name})")
                        return {"id": user.id, "telegram_id": user.telegram_id}
                        
                except Exception as e:
                    logger.error(f"❌ Ошибка добавления пользователя: {e}")
                    # Возвращаем заглушку, чтобы бот продолжал работу
                    return {"id": telegram_id, "telegram_id": telegram_id}
            
            def add_mood_log(self, user_id, mood_score=None, message=None):
                """Добавить запись настроения"""
                try:
                    with self.get_db_session() as session:
                        log = MoodLog(
                            user_id=user_id,
                            mood_score=mood_score,
                            user_message=message
                        )
                        session.add(log)
                        session.commit()
                        session.refresh(log)
                        
                        logger.info(f"📊 Запись настроения: user={user_id}, score={mood_score}")
                        return {"id": log.id, "user_id": log.user_id}
                        
                except Exception as e:
                    logger.error(f"❌ Ошибка добавления записи настроения: {e}")
                    return {"id": 0, "user_id": user_id}
            
            def get_user_stats(self, user_id):
                """Получить статистику пользователя"""
                try:
                    with self.get_db_session() as session:
                        # Количество записей
                        count = session.query(MoodLog).filter(
                            MoodLog.user_id == user_id
                        ).count()
                        
                        # Среднее настроение
                        avg_mood = session.query(func.avg(MoodLog.mood_score)).filter(
                            MoodLog.user_id == user_id,
                            MoodLog.mood_score.isnot(None)
                        ).scalar()
                        
                        # Последние записи
                        recent = session.query(MoodLog).filter(
                            MoodLog.user_id == user_id
                        ).order_by(MoodLog.created_at.desc()).limit(5).all()
                        
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
                        
                except Exception as e:
                    logger.error(f"❌ Ошибка получения статистики: {e}")
                    return {
                        "total_records": 0,
                        "avg_mood": None,
                        "recent_logs": []
                    }
        
        # Создаем реальный менеджер БД
        db_manager = DatabaseManager()
        
    except ImportError as e:
        logger.error(f"❌ Не удалось импортировать SQLAlchemy: {e}")
        # Создаем заглушку если нет SQLAlchemy
        from database import DummyDBManager
        db_manager = DummyDBManager()
        USE_REAL_DB = False
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации реальной БД: {e}")
        # Создаем заглушку при любой ошибке
        from database import DummyDBManager
        db_manager = DummyDBManager()
        USE_REAL_DB = False

# Экспортируем db_manager
__all__ = ['db_manager']
