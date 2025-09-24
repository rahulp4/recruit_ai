from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class PostgresManager:
    """Manages PostgreSQL database connection and sessions."""
    def __init__(self, db_uri):
        self.engine = None
        self.Session = None
        self.db_uri = db_uri
        self._connect()

    def _connect(self):
        """Establishes the database connection."""
        try:
            self.engine = create_engine(self.db_uri)
            # Test connection
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            self.Session = sessionmaker(bind=self.engine)
            logger.info("Successfully connected to PostgreSQL.")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}", exc_info=True)
            raise

    def get_session(self):
        """Returns a new SQLAlchemy session."""
        if not self.Session:
            raise RuntimeError("Database session not initialized. Call _connect() first.")
        return self.Session()

    def close_engine(self):
        """Closes the database engine."""
        if self.engine:
            self.engine.dispose()
            logger.info("PostgreSQL engine disposed.")

# Global instance (will be initialized in app.py)
postgres_manager = None

def init_db_manager(app):
    """Initializes the global PostgresManager instance."""
    global postgres_manager
    postgres_manager = PostgresManager(app.config['SQLALCHEMY_DATABASE_URI'])
    logger.info("PostgresManager initialized.")

def get_db_session():
    """Helper to get a database session from the global manager."""
    if not postgres_manager:
        raise RuntimeError("PostgresManager not initialized. Call init_db_manager() first.")
    return postgres_manager.get_session()