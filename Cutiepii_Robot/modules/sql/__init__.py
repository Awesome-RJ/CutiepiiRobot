"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (c) 2021-2026, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2026, Yūki - Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import time
from contextlib import contextmanager
from functools import wraps
from typing import Generator, Callable, Any

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, Query, Session
from sqlalchemy.pool import QueuePool, Pool
from sqlalchemy.exc import SQLAlchemyError, OperationalError, DisconnectionError
from Cutiepii_Robot import DB_URL, LOGGER

# Import psycopg2 for transaction status checking
try:
    import psycopg2
    import psycopg2.extensions
except ImportError:
    psycopg2 = None


class CachingQuery(Query):
    """Custom Query class with caching support"""

    def __init__(self, *args, cache=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = cache or {}

    def __iter__(self):
        """
        Overrides the __iter__ method of the parent class to implement caching.

        Returns:
            iter: An iterator over the cached query results.
        """
        cache_key = self.cache_key()
        result = self.cache.get(cache_key)

        if result is None:
            result = list(super().__iter__())
            self.cache[cache_key] = result

        return iter(result)

    def cache_key(self):
        """Generate cache key from query"""
        try:
            stmt = self.with_labels().statement
            compiled = stmt.compile()
            params = compiled.params
            return " ".join([str(compiled)] + [str(params[k]) for k in sorted(params)])
        except Exception:
            # Fallback if compilation fails
            return str(self)


# Fix Heroku postgres:// to postgresql://
if DB_URL and DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)


@event.listens_for(Pool, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Set SQLite pragmas for better performance (if using SQLite)"""
    try:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-64000")
        cursor.close()
    except Exception:
        pass  # Not SQLite, skip


@event.listens_for(Pool, "connect")
def handle_postgresql_connection(dbapi_conn, connection_record):
    """Handle PostgreSQL connection setup and rollback failed transactions"""
    if psycopg2 and isinstance(dbapi_conn, psycopg2.extensions.connection):
        try:
            # Ensure we start with a clean transaction state
            if dbapi_conn.status == psycopg2.extensions.STATUS_IN_TRANSACTION:
                try:
                    dbapi_conn.rollback()
                except Exception:
                    # If rollback fails, try to reset the connection
                    try:
                        dbapi_conn.reset()
                    except Exception:
                        pass
        except Exception:
            pass  # Ignore errors during connection setup


@event.listens_for(Pool, "checkout")
def check_connection(dbapi_conn, connection_record, connection_proxy):
    """Verify connection is alive on checkout and rollback failed transactions"""
    try:
        # Rollback any failed transactions first (PostgreSQL requirement)
        if psycopg2 and hasattr(dbapi_conn, 'status'):
            try:
                # Check if connection is in a failed transaction state
                if dbapi_conn.status == psycopg2.extensions.STATUS_IN_TRANSACTION:
                    dbapi_conn.rollback()
            except Exception:
                pass  # Ignore rollback errors if already clean
        
        cursor = dbapi_conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
    except Exception as e:
        # If there's a transaction error, try to rollback
        try:
            if hasattr(dbapi_conn, 'rollback'):
                dbapi_conn.rollback()
        except Exception:
            pass
        raise DisconnectionError("Connection lost, will reconnect")


def retry_on_db_error(max_retries: int = 3, delay: float = 1.0) -> Callable:
    """Decorator to retry database operations on failure"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (OperationalError, DisconnectionError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        LOGGER.warning(
                            f"[SQL] Database operation failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying..."
                        )
                        time.sleep(delay * (attempt + 1))
                    else:
                        LOGGER.error(f"[SQL] Database operation failed after {max_retries} attempts: {e}")
                except SQLAlchemyError as e:
                    LOGGER.error(f"[SQL] Database error in {func.__name__}: {e}")
                    raise
            raise last_exception
        return wrapper
    return decorator


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations with automatic rollback on error"""
    session = SESSION()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        LOGGER.error(f"[SQL] Session rollback due to: {e}")
        raise
    finally:
        session.close()


def start() -> scoped_session:
    """Initialize database connection and return scoped session"""
    try:
        # Create engine with improved connection pooling
        engine = create_engine(
            DB_URL,
            poolclass=QueuePool,
            pool_size=20,  # Increased from 15 for higher concurrency
            max_overflow=40,  # Increased from 30
            pool_pre_ping=True,  # Enable connection health checks
            pool_recycle=1800,   # Recycle connections after 30 minutes (reduced from 1 hour)
            pool_timeout=30,  # Connection timeout
            echo=False,  # Set to True for SQL debugging
            connect_args={
                "application_name": "CutiepiiRobot",
                "options": "-c timezone=utc -c statement_timeout=30000",
                "connect_timeout": 10,  # Connection timeout in seconds
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5,
            },
            execution_options={
                "isolation_level": "READ COMMITTED"  # Better concurrency
            }
        )
        
        LOGGER.info("[PostgreSQL] Connecting to database...")
        
        # Add event listener to handle connection errors and rollback failed transactions
        @event.listens_for(engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Handle connection errors and rollback failed transactions"""
            if psycopg2 and isinstance(dbapi_conn, psycopg2.extensions.connection):
                try:
                    # Ensure connection starts in a clean state
                    if dbapi_conn.status == psycopg2.extensions.STATUS_IN_TRANSACTION:
                        try:
                            dbapi_conn.rollback()
                        except Exception:
                            # If rollback fails, connection might be broken - will be handled by pool
                            pass
                except Exception:
                    pass  # Ignore errors during connection setup
        
        # Bind metadata and create tables
        BASE.metadata.bind = engine
        
        # Create tables with retry logic and proper transaction handling
        max_retries = 3
        for attempt in range(max_retries):
            try:
                BASE.metadata.create_all(engine)
                LOGGER.info("[PostgreSQL] Tables created/verified successfully")
                break
            except Exception as e:
                error_str = str(e)
                if "permission denied" in error_str.lower() or "insufficientprivilege" in error_str.lower():
                    # On managed databases like Render, user might not have CREATE TABLE permission
                    # Tables may need to be created manually or by database admin
                    LOGGER.warning(f"[PostgreSQL] Permission denied for table creation. Tables may need to be created manually or by database admin.")
                    LOGGER.warning(f"[PostgreSQL] Error: {e}")
                    # Continue anyway - tables might already exist or will be created by admin
                    break
                elif "InFailedSqlTransaction" in error_str or "current transaction is aborted" in error_str.lower():
                    LOGGER.warning(f"[PostgreSQL] Transaction error during table creation (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        # Wait before retry and create a new connection
                        time.sleep(2)
                        # Force pool to create a fresh connection
                        engine.dispose()
                        continue
                    else:
                        LOGGER.error(f"[PostgreSQL] Failed to create tables after {max_retries} attempts")
                        raise
                else:
                    # Different error, don't retry
                    LOGGER.error(f"[PostgreSQL] Error creating tables: {e}")
                    raise
        
        # Create scoped session
        session = scoped_session(
            sessionmaker(
                bind=engine,
                autoflush=False,
                autocommit=False,
                expire_on_commit=False,
                query_cls=CachingQuery
            )
        )
        
        LOGGER.info("[PostgreSQL] ✅ Connection successful!")
        LOGGER.info(f"[PostgreSQL] Pool size: 15, Max overflow: 30, Timeout: 30s")
        return session
        
    except Exception as e:
        LOGGER.error(f"[PostgreSQL] ❌ Connection failed: {e}")
        raise


# Create declarative base
BASE = declarative_base()

# Helper function to safely create tables (handles permission errors)
def safe_create_table(table, checkfirst=True):
    """Safely create a table, handling permission errors gracefully"""
    try:
        table.create(checkfirst=checkfirst)
    except Exception as e:
        error_str = str(e)
        if "permission denied" in error_str.lower() or "insufficientprivilege" in error_str.lower():
            # Table creation is handled by BASE.metadata.create_all() in start()
            # Permission errors are expected on managed databases like Render
            LOGGER.debug(f"[SQL] Table {table.name} creation skipped (permission or already exists): {e}")
        elif "already exists" in error_str.lower() or "duplicate" in error_str.lower():
            # Table already exists, which is fine
            LOGGER.debug(f"[SQL] Table {table.name} already exists")
        else:
            # Other errors should be logged
            LOGGER.warning(f"[SQL] Failed to create table {table.name}: {e}")

# Initialize session
try:
    SESSION: scoped_session = start()
except Exception as e:
    LOGGER.exception(f"[PostgreSQL] Fatal error during initialization: {e}")
    exit(1)
