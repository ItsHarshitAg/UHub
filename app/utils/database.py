import os
import time
import logging
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError, ProgrammingError

logger = logging.getLogger(__name__)

def wait_for_db(app, max_retries=5, retry_interval=2):
    """
    Wait for the database to be available.
    Useful when deploying with PostgreSQL on Render where the database
    might not be immediately available.
    """
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    
    # Skip the waiting process for SQLite
    if 'sqlite' in db_url:
        return True
    
    engine = create_engine(db_url)
    
    for attempt in range(max_retries):
        try:
            # Try to connect and run a simple query
            with engine.connect() as connection:
                connection.execute("SELECT 1")
            logger.info("Database connection established successfully")
            return True
        except (OperationalError, ProgrammingError) as e:
            logger.warning(f"Database connection attempt {attempt+1}/{max_retries} failed: {e}")
            if attempt + 1 < max_retries:
                logger.info(f"Waiting {retry_interval} seconds before retrying...")
                time.sleep(retry_interval)
    
    logger.error(f"Could not connect to the database after {max_retries} attempts")
    return False
