import os
import time
import logging
from sqlalchemy import create_engine, text
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
    
    try:
        # Log the database type we're connecting to (without credentials)
        if '@' in db_url:
            db_type = db_url.split('@')[0].split('://')[0] 
            db_host = db_url.split('@')[1].split('/')[0]
            logger.info(f"Attempting connection to {db_type} database at {db_host}")
        else:
            logger.info(f"Attempting connection to database: {db_url}")
        
        # Create engine with a reasonable timeout
        engine = create_engine(db_url, connect_args={"connect_timeout": 5})
        
        for attempt in range(max_retries):
            try:
                # Try to connect and run a simple query using SQLAlchemy 2.0 syntax
                with engine.connect() as connection:
                    connection.execute(text("SELECT 1"))
                logger.info("Database connection established successfully")
                return True
            except (OperationalError, ProgrammingError) as e:
                logger.warning(f"Database connection attempt {attempt+1}/{max_retries} failed: {e}")
                if attempt + 1 < max_retries:
                    logger.info(f"Waiting {retry_interval} seconds before retrying...")
                    time.sleep(retry_interval)
    except Exception as e:
        logger.error(f"Error setting up database connection: {e}")
        return False
    
    logger.error(f"Could not connect to the database after {max_retries} attempts")
    return False
