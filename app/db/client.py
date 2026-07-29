"""
Neon PostgreSQL connection pool client.
Uses psycopg2 ThreadedConnectionPool for efficient connection reuse.
Falls back gracefully when DATABASE_URL is not set (in-memory mode).
"""
import logging
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import psycopg2
    from psycopg2.pool import ThreadedConnectionPool
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logger.warning("psycopg2 not installed — running in memory-only mode")

_pool: Optional[object] = None


def init_db(database_url: str) -> bool:
    """
    Initialize the Neon PostgreSQL connection pool.

    Args:
        database_url: Full PostgreSQL connection string (e.g. from Neon)

    Returns:
        True if connected successfully, False otherwise
    """
    global _pool

    if not PSYCOPG2_AVAILABLE:
        logger.warning("psycopg2 not available — skipping DB init")
        return False

    if not database_url:
        logger.warning("DATABASE_URL not set — running in memory-only mode")
        return False

    try:
        _pool = ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=database_url,
            # Neon requires SSL
            sslmode="require"
        )
        # Smoke test
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        logger.info("[OK] Neon PostgreSQL connected and pool initialized")
        return True
    except Exception as e:
        logger.error(f"[FAIL] Failed to connect to Neon: {e}")
        _pool = None
        return False


@contextmanager
def get_db():
    """
    Context manager to get a DB connection from the pool.
    Automatically commits on success and rolls back on error.
    """
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call init_db() first.")

    conn = _pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)


def is_connected() -> bool:
    """Return True if the DB pool is active."""
    return _pool is not None


def close_db():
    """Gracefully close all connections in the pool."""
    global _pool
    if _pool is not None:
        try:
            _pool.closeall()
            logger.info("Database connection pool closed")
        except Exception as e:
            logger.error(f"Error closing DB pool: {e}")
        finally:
            _pool = None
