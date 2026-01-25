from app.db.base_class import Base

from app.models.contact import Contact
from app.models.user import User
from app.models.faucet_request import FaucetRequest
from app.models.survey import Survey, SurveyFollowUp

from app.models.token import TokenHolder, TokenActivity, TokenMonthlyStats
from app.models.personal_fund import PersonalFund, FundTransaction, FundInvestment
from app.models.governance import Proposal, Vote, VoterStats
from app.models.protocol import DeFiProtocol, ProtocolAPYHistory
from app.models.preferences import UserPreference, UserProtocolDeposit
from app.models.treasury import (
    TreasuryStats, FundFeeRecord, EarlyRetirementRequest, TreasuryWithdrawal
)
from app.models.blockchain import BlockchainEvent
from app.models.notification import Notification
from app.models.analytics import DailySnapshot

__all__ = ["Base"]