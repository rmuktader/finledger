"""Domain services for the financial ledger system."""

import re
from dataclasses import replace
from datetime import date
from decimal import Decimal
from typing import Dict, List

from .exceptions import CategoryMappingError, AggregationError
from .models import (
    AccountType,
    Ledger,
    LedgerEntry,
    MonthlyAggregate,
    TransactionCategory,
)


class LedgerTransformationService:
    """Transform bank-specific transactions to unified LedgerEntry format."""
    
    def from_cc_transaction(self, txn: any, stmt: any) -> LedgerEntry:
        """
        Transform credit card transaction to ledger entry.
        
        Args:
            txn: Credit card transaction from ccparse
            stmt: Credit card statement from ccparse
            
        Returns:
            LedgerEntry with normalized data
        """
        transaction_id = self._generate_id(
            txn.post_date,
            txn.description,
            txn.amount,
            AccountType.CREDIT_CARD
        )
        
        return LedgerEntry(
            transaction_id=transaction_id,
            date=txn.post_date,
            description=txn.description,
            amount=txn.amount,  # Positive = spend, Negative = payment/credit
            account_type=AccountType.CREDIT_CARD,
            category=TransactionCategory.UNCATEGORIZED,
            source_statement=getattr(stmt, 'filename', 'unknown'),
        )
    
    def from_checking_transaction(self, txn: any, stmt: any) -> LedgerEntry:
        """
        Transform checking transaction to ledger entry.
        
        Args:
            txn: Checking transaction from chkparse
            stmt: Checking statement from chkparse
            
        Returns:
            LedgerEntry with normalized data
        """
        # Convert checking transaction types to amount sign
        # Credits (deposits) = negative (income)
        # Debits (payments/withdrawals) = positive (expense)
        amount = txn.amount
        
        # Check transaction type to determine sign
        txn_type_str = str(txn.transaction_type.value if hasattr(txn.transaction_type, 'value') else txn.transaction_type)
        
        if any(credit_type in txn_type_str for credit_type in ['DEPOSIT', 'CREDIT']):
            amount = -amount  # Income = negative
        
        transaction_id = self._generate_id(
            txn.posting_date,
            txn.description,
            amount,
            AccountType.CHECKING
        )
        
        return LedgerEntry(
            transaction_id=transaction_id,
            date=txn.posting_date,
            description=txn.description,
            amount=amount,
            account_type=AccountType.CHECKING,
            category=TransactionCategory.UNCATEGORIZED,
            source_statement=getattr(stmt, 'filename', 'unknown'),
        )
    
    def _generate_id(
        self,
        txn_date: date,
        description: str,
        amount: Decimal,
        account_type: AccountType
    ) -> str:
        """
        Generate unique transaction ID.
        
        Composite key: date + description + amount + account_type
        """
        # Truncate description to 50 chars and remove special characters
        clean_desc = re.sub(r'[^a-zA-Z0-9]', '', description[:50])
        return f"{txn_date.isoformat()}_{clean_desc}_{amount}_{account_type.value}"


class CategoryMappingService:
    """Map transaction descriptions to categories using configurable rules."""
    
    def __init__(self, category_patterns: Dict[str, List[str]]):
        """
        Initialize with category mapping patterns.
        
        Args:
            category_patterns: Dict mapping category names to regex patterns
                Example: {"UTILITIES": ["WATER", "ELECTRIC"], ...}
        """
        self.category_patterns = category_patterns
    
    def categorize(self, entry: LedgerEntry) -> LedgerEntry:
        """
        Categorize a ledger entry based on description patterns.
        
        Args:
            entry: LedgerEntry to categorize
            
        Returns:
            LedgerEntry with updated category
            
        Raises:
            CategoryMappingError: If categorization fails
        """
        try:
            for category_name, patterns in self.category_patterns.items():
                # Convert category name to enum
                try:
                    category = TransactionCategory[category_name]
                except KeyError:
                    continue  # Skip unknown categories
                
                # Check if any pattern matches
                for pattern in patterns:
                    if re.search(pattern, entry.description, re.IGNORECASE):
                        return replace(entry, category=category)
            
            # No match found - remains UNCATEGORIZED
            return entry
            
        except Exception as e:
            raise CategoryMappingError(f"Failed to categorize entry: {e}") from e


class AggregationService:
    """Compute monthly and yearly aggregates from ledger entries."""
    
    def compute_monthly_aggregates(
        self,
        ledger: Ledger,
        year: int
    ) -> List[MonthlyAggregate]:
        """
        Compute monthly aggregates for all categories in a specific year.
        
        Args:
            ledger: Ledger containing all entries
            year: Year to compute aggregates for
            
        Returns:
            List of MonthlyAggregate objects (one per month per category)
            
        Raises:
            AggregationError: If computation fails
        """
        try:
            aggregates = []
            
            # Process each category (except UNCATEGORIZED)
            for category in TransactionCategory:
                if category == TransactionCategory.UNCATEGORIZED:
                    continue
                
                running_total = Decimal("0")
                
                # Process each month
                for month in range(1, 13):
                    # Get entries for this month and category
                    entries = [
                        e for e in ledger.entries
                        if e.date.year == year
                        and e.date.month == month
                        and e.category == category
                    ]
                    
                    # Calculate monthly total
                    monthly_total = sum((e.amount for e in entries), Decimal("0"))
                    running_total += monthly_total
                    
                    # Create aggregate
                    aggregates.append(MonthlyAggregate(
                        year=year,
                        month=month,
                        category=category,
                        total=monthly_total,
                        running_total=running_total,
                    ))
            
            return aggregates
            
        except Exception as e:
            raise AggregationError(f"Failed to compute aggregates: {e}") from e
    
    def compute_yearly_total(
        self,
        ledger: Ledger,
        year: int,
        category: TransactionCategory
    ) -> Decimal:
        """
        Compute yearly total for a specific category.
        
        Args:
            ledger: Ledger containing all entries
            year: Year to compute total for
            category: Category to sum
            
        Returns:
            Total amount for the year and category
        """
        entries = [
            e for e in ledger.entries
            if e.date.year == year and e.category == category
        ]
        return sum((e.amount for e in entries), Decimal("0"))
