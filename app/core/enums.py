from enum import IntEnum, Enum

class ProposalType(IntEnum):
    GENERAL = 0
    EARLY_RETIREMENT = 1
    TREASURY = 2
    PARAMETER = 3

class ProposalStatus(str, Enum):
    PENDING = "pending"  # Antes de start_time
    ACTIVE = "active"  # Entre start_time y end_time
    QUEUED = "queued"  # Aprobada pero antes de execution_time
    SUCCEEDED = "succeeded"  # Lista para ejecutar
    DEFEATED = "defeated"  # No pasó o no llegó a quorum
    EXECUTED = "executed"  # Ya ejecutada
    CANCELLED = "cancelled"  # Cancelada

class RiskLevel(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

class RoutingStrategy(IntEnum):
    MANUAL = 0
    BEST_APY = 1
    RISK_ADJUSTED = 2
    DIVERSIFIED = 3

class FundStatus(str, Enum):
    NO_FUND = "no_fund"
    ACCUMULATING = "accumulating"  # Antes de timelock_end
    READY_FOR_RETIREMENT = "ready"  # Después de timelock_end
    EARLY_APPROVED = "early_approved"  # Early retirement aprobado
    RETIRED = "retired"  # Ya en fase de retiro

class FundTransactionType(str, Enum):
    """Tipos de transacciones de fondos"""
    INITIAL_DEPOSIT = "initial_deposit"
    MONTHLY_DEPOSIT = "monthly_deposit"
    EXTRA_DEPOSIT = "extra_deposit"
    INVEST = "invest"
    DIVEST = "divest"
    WITHDRAWAL = "withdrawal"
    AUTO_WITHDRAWAL = "auto_withdrawal"
    EMERGENCY_WITHDRAWAL = "emergency_withdrawal"
    FEE_PAYMENT = "fee_payment"

class TokenActivityType(str, Enum):
    """Tipos de actividad del token GERAS"""
    MINTED = "minted"
    BURNED = "burned"
    RENEWED = "renewed"
    PROPOSAL_CREATED = "proposal_created"
    VOTE_CAST = "vote_cast"
    EARLY_RETIREMENT_REQUESTED = "early_retirement_requested"
    EARLY_RETIREMENT_APPROVED = "early_retirement_approved"
    FUND_DEPOSIT = "fund_deposit"
    FUND_WITHDRAWAL = "fund_withdrawal"

class NotificationType(str, Enum):
    TOKEN_MINTED = "token_minted"
    TOKEN_BURNED = "token_burned"
    TOKEN_RENEWED = "token_renewed"
    TOKEN_BURN_WARNING = "token_burn_warning"  # 7 días antes

    FUND_CREATED = "fund_created"
    DEPOSIT_RECEIVED = "deposit_received"
    WITHDRAWAL_EXECUTED = "withdrawal_executed"
    AUTO_WITHDRAWAL_EXECUTED = "auto_withdrawal_executed"
    RETIREMENT_READY = "retirement_ready"

    PROPOSAL_CREATED = "proposal_created"
    VOTE_CAST = "vote_cast"
    PROPOSAL_EXECUTED = "proposal_executed"
    PROPOSAL_CANCELLED = "proposal_cancelled"

    EARLY_RETIREMENT_REQUESTED = "early_retirement_requested"
    EARLY_RETIREMENT_APPROVED = "early_retirement_approved"
    EARLY_RETIREMENT_REJECTED = "early_retirement_rejected"

    INVESTMENT_MADE = "investment_made"
    INVESTMENT_WITHDRAWN = "investment_withdrawn"

    SYSTEM_ANNOUNCEMENT = "system_announcement"
    SECURITY_ALERT = "security_alert"

class BlockchainEventType(str, Enum):
    TRANSFER = "Transfer"
    TOKENS_BURNED = "TokensBurned"
    TOKENS_RENEWED = "TokensRenewed"
    BATCH_BURN_COMPLETED = "BatchBurnCompleted"
    BATCH_RENEW_COMPLETED = "BatchRenewCompleted"
    ACTIVITY_RECORDED = "ActivityRecorded"

    INITIALIZED = "Initialized"
    DEPOSITED = "Deposited"
    MONTHLY_DEPOSITED = "MonthlyDeposited"
    EXTRA_DEPOSITED = "ExtraDeposited"
    WITHDRAWN = "Withdrawn"
    AUTO_WITHDRAWAL_EXECUTED = "AutoWithdrawalExecuted"
    RETIREMENT_STARTED = "RetirementStarted"
    INVESTED_IN_PROTOCOL = "InvestedInProtocol"
    WITHDRAWN_FROM_PROTOCOL = "WithdrawnFromProtocol"

    PROPOSAL_CREATED = "ProposalCreated"
    VOTE_CAST = "VoteCast"
    PROPOSAL_EXECUTED = "ProposalExecuted"
    PROPOSAL_CANCELLED = "ProposalCancelled"

    FEE_RECEIVED = "FeeReceived"
    EARLY_RETIREMENT_REQUESTED = "EarlyRetirementRequested"
    EARLY_RETIREMENT_APPROVED = "EarlyRetirementApproved"
    EARLY_RETIREMENT_REJECTED = "EarlyRetirementRejected"
    FEES_WITHDRAWN = "FeesWithdrawn"

    PROTOCOL_ADDED = "ProtocolAdded"
    PROTOCOL_UPDATED = "ProtocolUpdated"
    PROTOCOL_VERIFIED = "ProtocolVerified"