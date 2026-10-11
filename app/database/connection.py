"""PostgreSQL Database connection and session management."""
import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from app.config import get_settings

logger = logging.getLogger("querymind.database")
settings = get_settings()

# Engine with pooling
try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={"connect_timeout": 5}
    )
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    engine = None

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency for obtaining a database session."""
    if engine is None:
        raise RuntimeError("Database engine is not initialized.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db_connection() -> dict:
    """Health check for PostgreSQL database connection."""
    if engine is None:
        return {"status": "unhealthy", "error": "Database engine not initialized"}
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();")).scalar()
            return {
                "status": "healthy",
                "database": "postgresql",
                "version": str(result),
                "url": settings.DATABASE_URL.split("@")[-1]  # Mask credentials
            }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}
