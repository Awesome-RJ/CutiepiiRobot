"""
Config Doctor Tool
Drift detection, environment validation, and startup connection checks for PostgreSQL & Redis.
"""

import os
import sys
import logging
from sqlalchemy import create_engine
from redis import StrictRedis

LOGGER = logging.getLogger(__name__)


def run_doctor():
    """Run configuration and database checks."""
    LOGGER.info("=" * 60)
    LOGGER.info("🩺 Starting ConfigDoctor validation checks...")
    LOGGER.info("=" * 60)

    # 1. Environment & Config Variables Validation
    required_vars = [
        "TOKEN",
        "API_ID",
        "API_HASH",
        "DATABASE_URL",
        "REDIS_URL"
    ]

    missing_vars = []
    # Check environment variables
    for var in required_vars:
        val = os.environ.get(var)
        if not val:
            # Fallback check from config.py if it exists
            try:
                from Cutiepii_Robot.config import Config
                if not hasattr(Config, var) or not getattr(Config, var):
                    missing_vars.append(var)
            except Exception:
                missing_vars.append(var)

    if missing_vars:
        LOGGER.error(f"❌ Configuration Drift/Validation Error: Missing required variables: {', '.join(missing_vars)}")
        LOGGER.error("Please set these variables in your environment or in config.py.")
        sys.exit(1)
    else:
        LOGGER.info("✅ All required config/environment variables are present.")

    # 2. Database URL Validation
    try:
        from Cutiepii_Robot.config import Config
        db_url = os.environ.get("DATABASE_URL") or getattr(Config, "DATABASE_URL", None)
        redis_url = os.environ.get("REDIS_URL") or getattr(Config, "REDIS_URL", None)
    except Exception:
        db_url = os.environ.get("DATABASE_URL")
        redis_url = os.environ.get("REDIS_URL")

    # 3. PostgreSQL Database Connection Check
    if db_url:
        # Convert postgres:// to postgresql:// if needed for SQLAlchemy compatibility
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        LOGGER.info("🔌 Testing PostgreSQL database connection...")
        try:
            engine = create_engine(db_url)
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            LOGGER.info("✅ PostgreSQL connection validation successful!")
        except Exception as e:
            LOGGER.error(f"❌ PostgreSQL connection failed: {e}")
            sys.exit(1)

    # 4. Redis Connection Check
    if redis_url:
        LOGGER.info("🔌 Testing Redis database connection...")
        try:
            redis = StrictRedis.from_url(redis_url, decode_responses=True)
            redis.ping()
            LOGGER.info("✅ Redis connection validation successful!")
        except Exception as e:
            LOGGER.error(f"❌ Redis connection failed: {e}")
            sys.exit(1)

    LOGGER.info("=" * 60)
    LOGGER.info("🩺 ConfigDoctor validation complete. System is healthy.")
    LOGGER.info("=" * 60)
