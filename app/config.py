"""QueryMind AI centralized configuration module."""
from functools import lru_cache
import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # App General
    APP_NAME: str = "QueryMind AI"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = Field(default="development", env="APP_ENV")
    APP_MODE: str = Field(default="demo", env="APP_MODE")  # 'demo' or 'live'
    
    # Paths
    BASE_DIR: Path = PROJECT_ROOT
    DATA_DIR: Path = PROJECT_ROOT / "data"
    MODELS_DIR: Path = PROJECT_ROOT / "models"
    REPORTS_DIR: Path = PROJECT_ROOT / "reports"
    LOGS_DIR: Path = PROJECT_ROOT / "logs"
    KNOWLEDGE_BASE_DIR: Path = PROJECT_ROOT / "knowledge_base"
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://neondb_owner:npg_4QRTamB0CKeD@ep-shy-darkness-b5aowtw4.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require",
        env="DATABASE_URL"
    )
    MAX_QUERY_ROWS: int = Field(default=500, env="MAX_QUERY_ROWS")
    QUERY_TIMEOUT_SECONDS: int = Field(default=15, env="QUERY_TIMEOUT_SECONDS")
    
    # LLM Settings
    GROQ_API_KEY: Optional[str] = Field(default=None, env="GROQ_API_KEY")
    GROQ_MODEL: str = Field(default="llama-3.3-70b-versatile", env="GROQ_MODEL")
    
    # Vector Search & Embeddings
    QDRANT_URL: str = Field(default="local", env="QDRANT_URL")
    QDRANT_PATH: Path = PROJECT_ROOT / "data" / "qdrant_storage"
    QDRANT_COLLECTION: str = Field(default="querymind_knowledge", env="QDRANT_COLLECTION")
    EMBEDDING_MODEL: str = Field(default="all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    RAG_TOP_K: int = Field(default=6, env="RAG_TOP_K")
    
    # Server & Client
    API_HOST: str = Field(default="127.0.0.1", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    FRONTEND_PORT: int = Field(default=8501, env="FRONTEND_PORT")

    class Config:
        env_file = str(PROJECT_ROOT / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    
    # Try reading from Streamlit Cloud secrets if running on Streamlit Cloud
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "DATABASE_URL" in st.secrets:
            cloud_db_url = st.secrets["DATABASE_URL"]
            if cloud_db_url and "your-host" not in cloud_db_url:
                settings.DATABASE_URL = str(cloud_db_url)
        if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
            settings.GROQ_API_KEY = str(st.secrets["GROQ_API_KEY"])
        if hasattr(st, "secrets") and "APP_MODE" in st.secrets:
            settings.APP_MODE = str(st.secrets["APP_MODE"])
    except Exception:
        pass

    # Ensure directories exist
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    settings.QDRANT_PATH.mkdir(parents=True, exist_ok=True)
    return settings
