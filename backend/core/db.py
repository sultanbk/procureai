"""
ProcureAI - File Summary

What it does:
Configures database connectivity, SQL sessions, and declarative bases using SQLAlchemy.

What it means:
The persistence foundation for storing supplier metadata, run histories, audit logs, and contract models.

Importance in Project:
High. Handles asynchronous connections, commits, rollbacks, and provides db context dependencies to API routes.
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event

from backend.core.config import DATABASE_URL as CONFIG_DATABASE_URL

# Read Database URL from env
DATABASE_URL = CONFIG_DATABASE_URL

# Convert standard sqlite URL to aiosqlite format for async compatibility
if DATABASE_URL.startswith("sqlite://"):
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")

# Create Async Engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    # SQLite-specific optimization for concurrent reads/writes
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)


@event.listens_for(engine.sync_engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
    if "sqlite" not in DATABASE_URL:
        return
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Declarative Base for models
class Base(DeclarativeBase):
    pass

# Dependency to get db session in routes
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
