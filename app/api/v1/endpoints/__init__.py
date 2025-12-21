from .auth import router as auth
from .contact import router as contact
from .users import router as users

# Si se añaden más endpoints (ej: contributions.py, health.py, etc.)
# from .contributions import router as contributions
# from .health import router as health

__all__ = [
    "auth",
    "contact",
    "users",
    # "others",
]