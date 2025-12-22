from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from typing import Dict, Any

from app.api.v1.deps import get_db, get_current_admin
from app.models.user import User
from app.models.faucet_request import FaucetRequest
from app.models.contact import Contact 

router = APIRouter()

@router.get("/admin/stats", response_model=Dict[str, Any])
async def get_admin_stats(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """
    Estadísticas detalladas del sistema (solo admin).
    Incluye:
    - Usuarios totales y wallets únicas
    - Proveedores de wallet detectados (Metamask, Binance, Rabby, etc.)
    - Solicitudes de faucet (total, éxito, fallidas)
    - Monto total dispensado
    - Monto por solicitud y por wallet
    """
    try:
        total_users = db.query(User).count()
        unique_wallets = db.query(distinct(User.wallet_address)).count()
        users_with_email = db.query(User).filter(User.email.isnot(None)).count()

        wallet_providers = db.query(
            func.upper(func.substr(User.user_agent, 1, instr(User.user_agent, '/') - 1)).label('provider'),
            func.count().label('count')
        ).filter(
            User.user_agent.isnot(None),
            User.user_agent != ''
        ).group_by('provider').order_by(func.count().desc()).limit(10).all()

        providers_dict = {provider: count for provider, count in wallet_providers}

        total_requests = db.query(FaucetRequest).count()
        successful_requests = db.query(FaucetRequest).filter(FaucetRequest.status == "success").count()
        failed_requests = db.query(FaucetRequest).filter(FaucetRequest.status == "failed").count()

        total_dispensed = db.query(func.coalesce(func.sum(FaucetRequest.amount), 0)).filter(
            FaucetRequest.status == "success"
        ).scalar() or 0

        avg_per_request = 0
        if successful_requests > 0:
            avg_per_request = total_dispensed / successful_requests

        top_wallets = db.query(
            FaucetRequest.wallet_address,
            func.sum(FaucetRequest.amount).label('total_received'),
            func.count().label('requests')
        ).filter(FaucetRequest.status == "success")\
         .group_by(FaucetRequest.wallet_address)\
         .order_by(func.sum(FaucetRequest.amount).desc())\
         .limit(5).all()

        top_wallets_list = [
            {"wallet": w, "total_usdc": float(total), "requests": requests}
            for w, total, requests in top_wallets
        ]

        total_contacts = db.query(Contact).count()
        unread_contacts = db.query(Contact).filter(Contact.is_read == False).count()

        return {
            "users": {
                "total": total_users,
                "unique_wallets": unique_wallets,
                "with_email": users_with_email,
                "top_wallet_providers": providers_dict  # ej: {"METAMASK": 120, "RABBY": 45, ...}
            },
            "faucet": {
                "total_requests": total_requests,
                "successful": successful_requests,
                "failed": failed_requests,
                "total_dispensed_usdc": float(total_dispensed),
                "average_per_request_usdc": round(float(avg_per_request), 6),
                "top_5_receivers": top_wallets_list
            },
            "contacts": {
                "total_messages": total_contacts,
                "unread": unread_contacts
            },
            "generated_at": func.now()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener estadísticas"
        ) from e