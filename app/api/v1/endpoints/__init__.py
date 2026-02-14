from .auth import router as auth
from .contact import router as contact
from .users import router as users
from .survey import router as survey 
from .stats import router as stats
from .funds import router as funds
from .tokens import router as tokens
from .governance import router as governance
from .protocols import router as protocols
from .treasury import router as treasury
from .preferences import router as preferences
from .blockchain import router as blockchain
from .analytics import router as analytics
from .notifications import router as notifications

__all__ = [
    "auth",
    "contact",
    "users",
    "survey",
    "stats",
    "funds",
    "tokens",
    "governance",
    "protocols",
    "treasury",
    "preferences",
    "blockchain",
    "analytics",
    "notifications",
]