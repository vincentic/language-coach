"""
Database configuration and connection
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT = os.getenv("DATABASE_PORT", "3306")
DATABASE_NAME = os.getenv("DATABASE_NAME", "polyglot_voice_coach")
DATABASE_USER = os.getenv("DATABASE_USER", "root")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "")

# Create database URL
DATABASE_URL = f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=os.getenv("DEBUG", "false").lower() == "true"
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    import app.database.models as models
    Base.metadata.create_all(bind=engine)
