import logging
from .celery_app import celery_app
from app.db.session import SessionLocal
from app.services.analytics_service import analytics_service

logger = logging.getLogger(__name__)

@celery_app.task
def create_daily_snapshot():
    db = SessionLocal()
    try:
        snapshot = analytics_service.create_snapshot(db)
        logger.info(f"📊 Daily snapshot created for {snapshot.snapshot_date}")
        return {"status": "success", "date": str(snapshot.snapshot_date)}
        
    except Exception as e:
        logger.error(f"Error creating snapshot: {e}", exc_info=True)
        raise
    finally:
        db.close()
