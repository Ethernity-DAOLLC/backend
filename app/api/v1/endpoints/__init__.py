from .auth import router as auth
from .contact import router as contact
from .users import router as users
from .survey import router as survey 
from .stats import router as stats 

__all__ = [
    "auth",
    "contact",
    "users",
    "survey", 
    "stats",  
]