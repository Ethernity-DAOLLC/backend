from app.db.base import Base
from app.models.user import User
from app.models.survey import Survey, SurveyFollowUp

from app.models.contact import Contact
from app.models.governance import (
    Proposal,
    Vote,
    VoterStats
)
from app.models.token import (
    TokenHolder,
    TokenActivity,
    TokenMonthlyStats
)
from app.models.personal_fund import (
    PersonalFund,
    FundTransaction,
    FundInvestment,
    FundStatus,
    TransactionType,
    InvestmentStatus
)
from app.models.treasury import (
    TreasuryStats,
    FundFeeRecord,
    EarlyRetirementRequest,
    TreasuryWithdrawal
)
from app.models.preferences import (
    UserPreference,
    UserProtocolDeposit
)
from app.models.protocol import (
    DeFiProtocol,
    ProtocolAPYHistory,
    ProtocolType
)
from app.models.notification import Notification
from app.models.blockchain import BlockchainEvent
from app.models.faucet_request import FaucetRequest
from app.models.analytics import (
    DailySnapshot,
    WeeklyReport,
    MonthlyReport,
    SystemMetric,
    UserActivityLog,
    SYSTEM_METRICS
)


__all__ = [
    # Base
    "Base",
    
    # Core
    "User",
    "Survey",
    "SurveyFollowUp",
    "Contact",
    
    # Governance
    "Proposal",
    "Vote",
    "VoterStats",
    
    # Token System
    "TokenHolder",
    "TokenActivity",
    "TokenMonthlyStats",
    
    # Personal Funds
    "PersonalFund",
    "FundTransaction",
    "FundInvestment",
    "FundStatus",
    "TransactionType",
    "InvestmentStatus",
    
    # Treasury
    "TreasuryStats",
    "FundFeeRecord",
    "EarlyRetirementRequest",
    "TreasuryWithdrawal",
    
    # Preferences
    "UserPreference",
    "UserProtocolDeposit",
    
    # DeFi Protocols
    "DeFiProtocol",
    "ProtocolAPYHistory",
    "ProtocolType",
    
    # Notifications
    "Notification",
    
    # Blockchain
    "BlockchainEvent",
    
    # Faucet
    "FaucetRequest",
    
    # Analytics
    "DailySnapshot",
    "WeeklyReport",
    "MonthlyReport",
    "SystemMetric",
    "UserActivityLog",
    "SYSTEM_METRICS",
]


"""
Este archivo sirve como punto de entrada centralizado para todos los modelos.

IMPORTANCIA:
1. Alembic necesita que todos los modelos estén importados para generar migraciones
2. SQLAlchemy necesita descubrir todas las tablas al iniciar
3. Facilita imports desde otros módulos: `from app.models import User, Proposal`

USO:
```python
# En lugar de:
from app.models.user import User
from app.models.governance import Proposal
from app.models.token import TokenHolder

# Puedes hacer:
from app.models import User, Proposal, TokenHolder
```

ORDEN DE IMPORTS:
Los imports están ordenados para respetar dependencias de ForeignKeys:
1. Base models (User, etc.)
2. Dependent models (Proposal depende de User)
3. Complex models (Treasury depende de PersonalFund)

TESTING:
```python
# Verificar que todos los modelos se importan correctamente
from app.models import *

print("Models available:", len(__all__))
print("Base imported:", Base)
print("User imported:", User)
# ... etc
```

ALEMBIC:
En alembic/env.py debes importar este archivo:
```python
from app.models import Base

target_metadata = Base.metadata
```

Esto asegura que Alembic vea todas las tablas.
"""