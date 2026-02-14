from sqlalchemy.orm import Session
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def init_db(db: Session = None) -> None:
    if db is None:
        db = SessionLocal()
    
    try:
        # Aquí puedes agregar datos iniciales
        # Por ejemplo, crear un usuario admin si no existe
        logger.info("✅ Base de datos inicializada")
    except Exception as e:
        logger.error(f"❌ Error inicializando datos: {e}")
        raise
    finally:
        if db:
            db.close()