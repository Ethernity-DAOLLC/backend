from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._engine = None
        self._session_factory = None
        self._initialize()
    
    def _initialize(self) -> None:
        connect_args = {}

        if self.settings.is_supabase:
            connect_args = {"sslmode": "require"}
            logger.info("🔒 SSL enabled for Supabase")

        self._engine = create_engine(
            self.settings.database_url_sync,
            pool_pre_ping=self.settings.DB_POOL_PRE_PING,
            pool_size=self.settings.DB_POOL_SIZE,
            max_overflow=self.settings.DB_MAX_OVERFLOW,
            pool_recycle=self.settings.DB_POOL_RECYCLE,
            pool_timeout=30,
            echo=self.settings.DB_ECHO,
            future=True,
            connect_args=connect_args,
            poolclass=pool.QueuePool,
        )

        self._session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self._engine,
            expire_on_commit=False,
        )
        self._add_event_listeners()
        logger.info("✅ Database engine initialized")
    
    def _add_event_listeners(self) -> None:
        @event.listens_for(self._engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            logger.debug("🔌 New database connection established")
        
        @event.listens_for(self._engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            logger.debug("📤 Connection checked out from pool")
        
        @event.listens_for(self._engine, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            logger.debug("📥 Connection returned to pool")
    
    @property
    def engine(self):
        return self._engine
    
    def get_session(self) -> Session:
        return self._session_factory()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def check_connection(self) -> bool:
        try:
            with self._engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def close(self) -> None:
        if self._engine:
            self._engine.dispose()
            logger.info("🔌 Database connections closed")

db_manager = DatabaseManager(settings)
engine = db_manager.engine
SessionLocal = db_manager.get_session