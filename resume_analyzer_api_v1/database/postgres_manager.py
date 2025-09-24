import logging
import time
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, DisconnectionError
# from sqlalchemy.pool import QueuePool # <--- REMOVE THIS IMPORT, no longer needed directly
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO) # Inherit from root or set explicitly

# Global instance for the database manager
postgres_manager = None

class PostgresManager:
    """
    Manages PostgreSQL database connection and sessions with robust connection pooling
    suitable for production environments.
    """
    def __init__(self, db_uri, pool_size, max_overflow, pool_recycle, pool_pre_ping, pool_timeout, connect_retries, retry_delay_seconds):
        self.engine = None
        self.Session = None
        self.db_uri = db_uri
        
        self._pool_size = pool_size
        self._max_overflow = max_overflow
        self._pool_recycle = pool_recycle
        self._pool_pre_ping = pool_pre_ping
        self._pool_timeout = pool_timeout
        
        self._connect_retries = connect_retries
        self._retry_delay_seconds = retry_delay_seconds
        
        self._connect()

    def _connect(self):
        """
        Establishes the database connection with retries and robust pooling configuration.
        """
        for attempt in range(self._connect_retries):
            try:
                self.engine = create_engine(
                    self.db_uri,
                    pool_size=self._pool_size,
                    max_overflow=self._max_overflow,
                    pool_recycle=self._pool_recycle,
                    pool_pre_ping=self._pool_pre_ping,
                    pool_timeout=self._pool_timeout,
                    # pool_class=QueuePool, # <--- REMOVE THIS LINE
                )
                
                with self.engine.connect() as connection:
                    connection.execute(text("SELECT 1"))
                
                self.Session = sessionmaker(bind=self.engine)
                logger.info(f"Successfully connected to PostgreSQL after {attempt + 1} attempt(s).")
                return 
            except (OperationalError, DisconnectionError) as e:
                logger.warning(f"Failed to connect to PostgreSQL (attempt {attempt + 1}/{self._connect_retries}): {e}")
                if attempt < self._connect_retries - 1:
                    logger.info(f"Retrying connection in {self._retry_delay_seconds} seconds...")
                    time.sleep(self._retry_delay_seconds)
                else:
                    logger.critical(f"FATAL: Exhausted all PostgreSQL connection retries. Application may not function correctly. Last error: {e}", exc_info=True)
                    raise 
            except Exception as e:
                logger.critical(f"FATAL: Unexpected error during PostgreSQL connection: {e}", exc_info=True)
                raise 

    def get_session(self):
        """Returns a new SQLAlchemy session from the configured pool."""
        if not self.Session:
            raise RuntimeError("Database session not initialized. Call _connect() first.")
        return self.Session()

    def close_engine(self):
        """
        Disposes of the database engine and closes all connections in the pool.
        Should be called when the application is shutting down.
        """
        if self.engine:
            self.engine.dispose()
            logger.info("PostgreSQL engine and all pooled connections disposed.")

def init_db_manager(app):
    """
    Initializes the global PostgresManager instance.
    This should be called once at application startup.
    """
    global postgres_manager
    if postgres_manager is None:
        postgres_manager = PostgresManager(
            db_uri=app.config['SQLALCHEMY_DATABASE_URI'],
            pool_size=app.config['DB_POOL_SIZE'],
            max_overflow=app.config['DB_MAX_OVERFLOW'],
            pool_recycle=app.config['DB_POOL_RECYCLE'],
            pool_pre_ping=app.config['DB_POOL_PRE_PING'],
            pool_timeout=app.config['DB_POOL_TIMEOUT'],
            connect_retries=app.config['DB_CONNECT_RETRIES'],
            retry_delay_seconds=app.config['DB_RETRY_DELAY_SECONDS']
        )
        logger.info("Global PostgresManager initialized with configurable pooling.")
    else:
        logger.info("Global PostgresManager already initialized.")


def get_db_session():
    """
    Helper to get a database session from the global manager.
    Ensure this is called from within a request context or managed lifecycle.
    """
    if postgres_manager is None:
        raise RuntimeError("PostgresManager not initialized. Call init_db_manager() in app startup.")
    return postgres_manager.get_session()