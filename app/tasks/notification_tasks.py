from datetime import datetime, timedelta
import logging

from .celery_app import celery_app
from app.db.session import SessionLocal
from app.services.token_service import token_service
from app.services.fund_service import fund_service
from app.services.notification_service import notification_service
from app.schemas.notification import NotificationCreate
from app.core.enums import NotificationType
from app.core.helpers import days_until_burn

logger = logging.getLogger(__name__)

@celery_app.task
def send_token_burn_warnings():
    db = SessionLocal()
    try:
        days_left = days_until_burn()
        if days_left != 7:
            return {"status": "skipped", "days_until_burn": days_left}

        inactive = token_service.get_inactive_holders(db)
        for holder in inactive:
            notif = NotificationCreate(
                user_id=holder.user_id,
                notification_type=NotificationType.TOKEN_BURN_WARNING.value,
                title="⚠️ Token Burn Warning",
                message=(
                    f"Your GERAS token will be burned in 7 days if you don't perform "
                    f"any activity. Make a deposit, vote on a proposal, or interact "
                    f"with your fund to keep your token active."
                ),
                related_entity_type="token",
                related_entity_id=holder.id
            )
            notification_service.create_notification(db, notif)
        logger.info(f"⚠️ Sent {len(inactive)} burn warnings")
        return {"status": "success", "warnings_sent": len(inactive)}
        
    except Exception as e:
        logger.error(f"Error sending burn warnings: {e}", exc_info=True)
        raise
    finally:
        db.close()

@celery_app.task
def send_proposal_notifications(proposal_id: int):
    db = SessionLocal()
    try:
        holders = token_service.get_all_holders(db, active_only=True)
        for holder in holders:
            notif = NotificationCreate(
                user_id=holder.user_id,
                notification_type=NotificationType.PROPOSAL_CREATED.value,
                title="📜 New Governance Proposal",
                message=f"A new proposal has been created. Review and vote on it!",
                related_entity_type="proposal",
                related_entity_id=proposal_id
            )
            notification_service.create_notification(db, notif)
        logger.info(f"📢 Sent proposal notifications to {len(holders)} holders")
        return {"status": "success", "notifications_sent": len(holders)}
        
    except Exception as e:
        logger.error(f"Error sending proposal notifications: {e}", exc_info=True)
        raise
    finally:
        db.close()

@celery_app.task
def send_retirement_ready_notifications():
    db = SessionLocal()
    try:
        ready_funds = fund_service.get_funds_ready_for_retirement(db)
        for fund in ready_funds:
            notif = NotificationCreate(
                user_id=fund.owner_id,
                notification_type=NotificationType.RETIREMENT_READY.value,
                title="🎉 Fund Ready for Retirement",
                message=(
                    f"Your retirement fund has reached maturity! You can now "
                    f"start the retirement phase and begin withdrawals."
                ),
                related_entity_type="fund",
                related_entity_id=fund.id
            )
            notification_service.create_notification(db, notif)
        logger.info(f"🎉 Sent {len(ready_funds)} retirement ready notifications")
        return {"status": "success", "notifications_sent": len(ready_funds)}
        
    except Exception as e:
        logger.error(f"Error sending retirement notifications: {e}", exc_info=True)
        raise
    finally:
        db.close()
