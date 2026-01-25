from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional

def calculate_fee(amount: Decimal) -> Decimal:
    return (amount * FEE_BASIS_POINTS) / BASIS_POINTS

def calculate_net_amount(gross_amount: Decimal) -> tuple[Decimal, Decimal]:
    fee = calculate_fee(gross_amount)
    net = gross_amount - fee
    return fee, net

def basis_points_to_percentage(bp: int) -> float:
    return bp / 100

def percentage_to_basis_points(percentage: float) -> int:
    return int(percentage * 100)

def get_proposal_status(
    start_time: datetime,
    end_time: datetime,
    execution_time: datetime,
    executed: bool,
    cancelled: bool,
    votes_for: Decimal,
    votes_against: Decimal,
    quorum_reached: bool
) -> str:
    if cancelled:
        return ProposalStatus.CANCELLED.value
    if executed:
        return ProposalStatus.EXECUTED.value
    
    now = datetime.utcnow()
    
    if now < start_time:
        return ProposalStatus.PENDING.value
    elif now <= end_time:
        return ProposalStatus.ACTIVE.value
    elif now < execution_time:
        if votes_for > votes_against and quorum_reached:
            return ProposalStatus.QUEUED.value
        else:
            return ProposalStatus.DEFEATED.value
    else:
        if votes_for > votes_against and quorum_reached:
            return ProposalStatus.SUCCEEDED.value
        else:
            return ProposalStatus.DEFEATED.value

def get_fund_status(
    retirement_started: bool,
    early_retirement_approved: bool,
    timelock_end: datetime
) -> str:
    if retirement_started:
        return FundStatus.RETIRED.value
    elif early_retirement_approved:
        return FundStatus.EARLY_APPROVED.value
    elif datetime.utcnow() >= timelock_end:
        return FundStatus.READY_FOR_RETIREMENT.value
    else:
        return FundStatus.ACCUMULATING.value

def days_until_burn() -> int:
    today = datetime.utcnow()
    if today.day > BURN_DAY:
        next_burn = datetime(today.year, today.month + 1 if today.month < 12 else 1, BURN_DAY)
        if today.month == 12:
            next_burn = datetime(today.year + 1, 1, BURN_DAY)
    else:
        next_burn = datetime(today.year, today.month, BURN_DAY)
    return (next_burn - today).days

def days_until_renew() -> int:
    today = datetime.utcnow()
    next_renew = datetime(
        today.year, 
        today.month + 1 if today.month < 12 else 1,
        RENEW_DAY
    )
    if today.month == 12:
        next_renew = datetime(today.year + 1, 1, RENEW_DAY)
    return (next_renew - today).days

def format_wallet_address(address: str) -> str:
    if not address or len(address) < 10:
        return address
    return f"{address[:6]}...{address[-4:]}"

def validate_wallet_address(address: str) -> bool:
    if not address:
        return False
    if not address.startswith('0x'):
        return False
    if len(address) != 42:
        return False
    try:
        int(address, 16)
        return True
    except ValueError:
        return False

def calculate_projected_balance(
    current_balance: Decimal,
    monthly_deposit: Decimal,
    months_remaining: int,
    annual_rate: int = 0
) -> Decimal:
    total_future_deposits = monthly_deposit * months_remaining
    return current_balance + total_future_deposits

def risk_level_name(level: int) -> str:
    return RISK_LEVELS.get(level, "Unknown")

def strategy_name(strategy_type: int) -> str:
    return STRATEGY_NAMES.get(strategy_type, "Unknown")

def proposal_type_name(proposal_type: int) -> str:
    return PROPOSAL_TYPE_NAMES.get(proposal_type, "Unknown")