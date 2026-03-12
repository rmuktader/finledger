"""Domain models for the financial ledger system."""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import List


class AccountType(str, Enum):
    """Type of financial account."""
    CREDIT_CARD = "CREDIT_CARD"
    CHECKING = "CHECKING"


class TransactionCategory(str, Enum):
    """Transaction expense categories."""
    UTILITIES = "UTILITIES"
    LOAN_PAYMENT = "LOAN_PAYMENT"
    MUNICIPAL_FEES = "MUNICIPAL_FEES"
    OFFICE_SUPPLIES = "OFFICE_SUPPLIES"
    PROFESSIONAL_SERVICES = "PROFESSIONAL_SERVICES"
    INSURANCE = "INSURANCE"
    RENT = "RENT"
    PAYROLL = "PAYROLL"
    TAXES = "TAXES"
    UNCATEGORIZED = "UNCATEGORIZED"


@dataclass(frozen=True)
class LedgerEntry:
    """
    A single transaction in the unified ledger.
    
    Entity with composite identity: (date, description, amount, account_type)
    """
    transaction_id: str          # Composite ID
    date: date
    description: str
    amount: Decimal              # Positive = expense, Negative = income/refund
    account_type: AccountType
    category: TransactionCategory
    source_statement: str        # PDF filename for auditability


@dataclass(frozen=True)
class MonthlyAggregate:
    """
    Monthly summary for a specific category.
    
    Value Object - immutable, derived from LedgerEntry collection.
    """
    year: int
    month: int                   # 1-12
    category: TransactionCategory
    total: Decimal
    running_total: Decimal       # Cumulative from Jan to current month


@dataclass
class Ledger:
    """
    Aggregate root for the financial ledger.
    
    Manages collection of LedgerEntry entities and enforces invariants.
    """
    entries: List[LedgerEntry] = field(default_factory=list)
    
    def add_entry(self, entry: LedgerEntry) -> None:
        """
        Add a ledger entry (idempotent by transaction_id).
        
        Invariant: No duplicate transaction IDs.
        """
        if not any(e.transaction_id == entry.transaction_id for e in self.entries):
            self.entries.append(entry)
    
    def get_entries_by_month(self, year: int, month: int) -> List[LedgerEntry]:
        """Get all entries for a specific month."""
        return [
            e for e in self.entries
            if e.date.year == year and e.date.month == month
        ]
    
    def get_entries_by_category(self, category: TransactionCategory) -> List[LedgerEntry]:
        """Get all entries for a specific category."""
        return [e for e in self.entries if e.category == category]
    
    def get_entries_by_year(self, year: int) -> List[LedgerEntry]:
        """Get all entries for a specific year."""
        return [e for e in self.entries if e.date.year == year]
    
    def get_total_by_category(self, category: TransactionCategory, year: int) -> Decimal:
        """Get total amount for a category in a specific year."""
        entries = [
            e for e in self.entries
            if e.category == category and e.date.year == year
        ]
        return sum((e.amount for e in entries), Decimal("0"))
