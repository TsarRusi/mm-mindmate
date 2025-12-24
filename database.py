# === ИСПРАВЛЕННЫЙ database.py ===
import os
import logging
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# ТОЛЬКО PostgreSQL на Render!
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    logger.critical("❌ DATABASE_URL не найден!")
    logger.critical("На Render: убедитесь, что база данных создана в render.yaml")
    logger.critical("Локально: установите DATABASE_URL в .env файле")
    raise ValueError("DATABASE_URL не настроен")

# Исправляем URL для SQLAlchemy (ВАЖНО!)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    logger.info("✅ URL базы данных исправлен для SQLAlchemy")

logger.info(f"🔗 Подключение к БД: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")

# Создаем движок PostgreSQL
try:
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
    
except Exception as e:
    logger.critical(f"❌ Ошибка создания движка БД: {e}")
    raise

@contextmanager
def get_db_session():
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

class DatabaseManager:
    def __init__(self):
        self.engine = engine
        self.Base = Base
    
    def init_db(self):
        """Создание таблиц с обработкой ошибок"""
        try:
            self.Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Таблицы БД созданы/проверены")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка создания таблиц: {e}")
            # Пробуем создать простую таблицу через raw SQL
            try:
                with self.engine.connect() as conn:
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
    
    def add_user(self, telegram_id, username=None, first_name=None):
        """Добавить пользователя с обработкой ошибок"""
        try:
            with get_db_session() as session:
                # Проверяем существование
                from sqlalchemy import text
                result = session.execute(
                    text("SELECT id FROM users WHERE telegram_id = :tid"),
                    {"tid": telegram_id}
                ).fetchone()
                
                if result:
                    # Обновляем last_active
                    session.execute(
                        text("UPDATE users SET last_active = NOW() WHERE telegram_id = :tid"),
                        {"tid": telegram_id}
                    )
                    return {"id": result[0], "telegram_id": telegram_id}
                
                # Создаем нового
                session.execute(
                    text("""
                        INSERT INTO users (telegram_id, username, first_name) 
                        VALUES (:tid, :uname, :fname)
                        RETURNING id
                    """),
                    {"tid": telegram_id, "uname": username, "fname": first_name}
                )
                result = session.execute(
                    text("SELECT id FROM users WHERE telegram_id = :tid"),
                    {"tid": telegram_id}
                ).fetchone()
                
                return {"id": result[0], "telegram_id": telegram_id}
                
        except Exception as e:
            logger.error(f"❌ Ошибка добавления пользователя: {e}")
            # Возвращаем заглушку, чтобы бот продолжал работать
            return {"id": 0, "telegram_id": telegram_id}

# Глобальный экземпляр
db_manager = DatabaseManager()
