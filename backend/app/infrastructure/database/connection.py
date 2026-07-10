"""Database connection setup using SQLAlchemy.

Provides async sessions and engines for SQLite via aiosqlite.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy database models."""


class DatabaseSessionManager:
    """Manages async database connections and session factories."""

    def __init__(self) -> None:
        self._engine = None
        self._sessionmaker = None

    def init(self, db_path: str) -> None:
        """Initialize the async engine and sessionmaker.

        Args:
            db_path: Path to the SQLite database file.
        """
        # Prefix for SQLite async driver is sqlite+aiosqlite
        url = f"sqlite+aiosqlite:///{db_path}"
        logger.info("Initializing async database connection: %s", url)

        self._engine = create_async_engine(
            url,
            echo=False,
            # SQLite specific optimizations for WAL mode and concurrent reads
            connect_args={"check_same_thread": False},
        )
        self._sessionmaker = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def close(self) -> None:
        """Dispose of the async engine."""
        if self._engine is None:
            return
        logger.info("Closing database connection.")
        await self._engine.dispose()
        self._engine = None
        self._sessionmaker = None

    async def create_all_tables(self) -> None:
        """Create all tables defined in metadata. Used for initial setup."""
        if self._engine is None:
            msg = "DatabaseSessionManager is not initialized."
            raise RuntimeError(msg)

        logger.info("Creating database tables if they do not exist.")
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Dependency generator for FastAPI to yield a session."""
        if self._sessionmaker is None:
            msg = "DatabaseSessionManager is not initialized."
            raise RuntimeError(msg)

        async with self._sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


# ─── Singleton Database Manager ───
db_manager = DatabaseSessionManager()
