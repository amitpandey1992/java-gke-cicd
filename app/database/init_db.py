"""Database initialization scripts."""

import logging
from app.database import postgres_client
from app.database.models import CREATE_FAILURES_TABLE, CREATE_FEEDBACK_LOG_TABLE

logger = logging.getLogger(__name__)

def create_tables(drop_existing: bool = False):
    """Creates the necessary database tables."""
    try:
        if drop_existing:
            logger.warning("Dropping existing tables...")
            postgres_client.execute_insert("DROP TABLE IF EXISTS feedback_log CASCADE")
            postgres_client.execute_insert("DROP TABLE IF EXISTS failures CASCADE")
            
        logger.info("Creating tables...")
        postgres_client.execute_insert(CREATE_FAILURES_TABLE)
        postgres_client.execute_insert(CREATE_FEEDBACK_LOG_TABLE)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}", exc_info=True)
        raise
