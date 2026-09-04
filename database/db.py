from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config.settings import settings

# Create the database engine (the connection to PostgreSQL)
engine = create_engine(settings.database_url)

# Create a session factory (used to talk to the database)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Base class for all our models
Base = declarative_base()


def get_db():
    """Creates a new database session. Use this in your code."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()