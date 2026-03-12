"""Unit tests for domain services."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

import pytest

from finledger.domain.exceptions import AggregationError, CategoryMappingError
from finledger.domain.models import (
    AccountType,
    Ledger,
    LedgerEntry,
    TransactionCategory,
)
from finledger.domain.services import (
    AggregationService,
    CategoryMappingService,
    LedgerTransformationService,
)


# Mock transaction objects for testing
@dataclass
class MockCCTransaction:
    post_date: date
    description: str
    amount: Decimal


@dataclass
class MockCheckingTransaction:
    posting_date: date
    description: str
    amount: Decimal
    transaction_type: str


@dataclass
class MockStatement:
    filename: str


class TestLedgerTransformationService:
    """Test LedgerTransformationService."""
    
    def test_from_cc_transaction(self):
        """Test transforming credit card transaction."""
        service = LedgerTransformationService()
        
        txn = MockCCTransaction(
            post_date=date(2024, 1, 15),
            description="Test Purchase",
            amount=Decimal("100.00"),
        )
        stmt = MockStatement(filename="test_cc.pdf")
        
        entry = service.from_cc_transaction(txn, stmt)
        
        assert entry.date == date(2024, 1, 15)
        assert entry.description == "Test Purchase"
        assert entry.amount == Decimal("100.00")
        assert entry.account_type == AccountType.CREDIT_CARD
        assert entry.category == TransactionCategory.UNCATEGORIZED
        assert entry.source_statement == "test_cc.pdf"
        assert entry.transaction_id.startswith("2024-01-15_")
    
    def test_from_checking_transaction_debit(self):
        """Test transforming checking debit transaction."""
        service = LedgerTransformationService()
        
        txn = MockCheckingTransaction(
            posting_date=date(2024, 1, 15),
            description="Payment",
            amount=Decimal("100.00"),
            transaction_type="ELECTRONIC_PAYMENT",
        )
        stmt = MockStatement(filename="test_chk.pdf")
        
        entry = service.from_checking_transaction(txn, stmt)
        
        assert entry.date == date(2024, 1, 15)
        assert entry.description == "Payment"
        assert entry.amount == Decimal("100.00")  # Positive = expense
        assert entry.account_type == AccountType.CHECKING
        assert entry.source_statement == "test_chk.pdf"
    
    def test_from_checking_transaction_credit(self):
        """Test transforming checking credit transaction."""
        service = LedgerTransformationService()
        
        txn = MockCheckingTransaction(
            posting_date=date(2024, 1, 15),
            description="Deposit",
            amount=Decimal("1000.00"),
            transaction_type="ELECTRONIC_DEPOSIT",
        )
        stmt = MockStatement(filename="test_chk.pdf")
        
        entry = service.from_checking_transaction(txn, stmt)
        
        assert entry.amount == Decimal("-1000.00")  # Negative = income
    
    def test_generate_id_is_consistent(self):
        """Test that same inputs generate same ID."""
        service = LedgerTransformationService()
        
        id1 = service._generate_id(
            date(2024, 1, 15),
            "Test Transaction",
            Decimal("100.00"),
            AccountType.CREDIT_CARD
        )
        id2 = service._generate_id(
            date(2024, 1, 15),
            "Test Transaction",
            Decimal("100.00"),
            AccountType.CREDIT_CARD
        )
        
        assert id1 == id2
    
    def test_generate_id_is_unique(self):
        """Test that different inputs generate different IDs."""
        service = LedgerTransformationService()
        
        id1 = service._generate_id(
            date(2024, 1, 15),
            "Transaction 1",
            Decimal("100.00"),
            AccountType.CREDIT_CARD
        )
        id2 = service._generate_id(
            date(2024, 1, 15),
            "Transaction 2",
            Decimal("100.00"),
            AccountType.CREDIT_CARD
        )
        
        assert id1 != id2


class TestCategoryMappingService:
    """Test CategoryMappingService."""
    
    def test_categorize_with_match(self):
        """Test categorizing entry with matching pattern."""
        patterns = {
            "UTILITIES": ["WATER", "ELECTRIC"],
            "LOAN_PAYMENT": ["LOAN", "MORTGAGE"],
        }
        service = CategoryMappingService(patterns)
        
        entry = LedgerEntry(
            transaction_id="test_id",
            date=date(2024, 1, 15),
            description="PROVIDENCE WATER SUPPLY",
            amount=Decimal("100.00"),
            account_type=AccountType.CREDIT_CARD,
            category=TransactionCategory.UNCATEGORIZED,
            source_statement="test.pdf",
        )
        
        categorized = service.categorize(entry)
        
        assert categorized.category == TransactionCategory.UTILITIES
    
    def test_categorize_case_insensitive(self):
        """Test that categorization is case-insensitive."""
        patterns = {
            "UTILITIES": ["water"],
        }
        service = CategoryMappingService(patterns)
        
        entry = LedgerEntry(
            transaction_id="test_id",
            date=date(2024, 1, 15),
            description="WATER COMPANY",
            amount=Decimal("100.00"),
            account_type=AccountType.CREDIT_CARD,
            category=TransactionCategory.UNCATEGORIZED,
            source_statement="test.pdf",
        )
        
        categorized = service.categorize(entry)
        
        assert categorized.category == TransactionCategory.UTILITIES
    
    def test_categorize_no_match(self):
        """Test categorizing entry with no matching pattern."""
        patterns = {
            "UTILITIES": ["WATER", "ELECTRIC"],
        }
        service = CategoryMappingService(patterns)
        
        entry = LedgerEntry(
            transaction_id="test_id",
            date=date(2024, 1, 15),
            description="RANDOM STORE",
            amount=Decimal("100.00"),
            account_type=AccountType.CREDIT_CARD,
            category=TransactionCategory.UNCATEGORIZED,
            source_statement="test.pdf",
        )
        
        categorized = service.categorize(entry)
        
        assert categorized.category == TransactionCategory.UNCATEGORIZED
    
    def test_categorize_regex_pattern(self):
        """Test categorizing with regex pattern."""
        patterns = {
            "LOAN_PAYMENT": ["TD Bank.*LOAN"],
        }
        service = CategoryMappingService(patterns)
        
        entry = LedgerEntry(
            transaction_id="test_id",
            date=date(2024, 1, 15),
            description="TD Bank N.A. LOAN PAYMENT",
            amount=Decimal("2000.00"),
            account_type=AccountType.CHECKING,
            category=TransactionCategory.UNCATEGORIZED,
            source_statement="test.pdf",
        )
        
        categorized = service.categorize(entry)
        
        assert categorized.category == TransactionCategory.LOAN_PAYMENT


class TestAggregationService:
    """Test AggregationService."""
    
    def test_compute_monthly_aggregates_single_category(self):
        """Test computing monthly aggregates for single category."""
        service = AggregationService()
        ledger = Ledger()
        
        # Add entries for January and February
        ledger.add_entry(LedgerEntry(
            transaction_id="jan_1",
            date=date(2024, 1, 15),
            description="Jan Utility",
            amount=Decimal("100.00"),
            account_type=AccountType.CREDIT_CARD,
            category=TransactionCategory.UTILITIES,
            source_statement="test.pdf",
        ))
        ledger.add_entry(LedgerEntry(
            transaction_id="feb_1",
            date=date(2024, 2, 15),
            description="Feb Utility",
            amount=Decimal("150.00"),
            account_type=AccountType.CREDIT_CARD,
            category=TransactionCategory.UTILITIES,
            source_statement="test.pdf",
        ))
        
        aggregates = service.compute_monthly_aggregates(ledger, 2024)
        
        # Find UTILITIES aggregates
        util_aggregates = [a for a in aggregates if a.category == TransactionCategory.UTILITIES]
        
        # Should have 12 months (one per month)
        assert len(util_aggregates) == 12
        
        # Check January
        jan_agg = next(a for a in util_aggregates if a.month == 1)
        assert jan_agg.total == Decimal("100.00")
        assert jan_agg.running_total == Decimal("100.00")
        
        # Check February
        feb_agg = next(a for a in util_aggregates if a.month == 2)
        assert feb_agg.total == Decimal("150.00")
        assert feb_agg.running_total == Decimal("250.00")  # Cumulative
        
        # Check March (no transactions)
        mar_agg = next(a for a in util_aggregates if a.month == 3)
        assert mar_agg.total == Decimal("0")
        assert mar_agg.running_total == Decimal("250.00")  # Stays same
    
    def test_compute_monthly_aggregates_multiple_categories(self):
        """Test computing aggregates for multiple categories."""
        service = AggregationService()
        ledger = Ledger()
        
        ledger.add_entry(LedgerEntry(
            transaction_id="util_1",
            date=date(2024, 1, 15),
            description="Utility",
            amount=Decimal("100.00"),
            account_type=AccountType.CREDIT_CARD,
            category=TransactionCategory.UTILITIES,
            source_statement="test.pdf",
        ))
        ledger.add_entry(LedgerEntry(
            transaction_id="loan_1",
            date=date(2024, 1, 15),
            description="Loan",
            amount=Decimal("2000.00"),
            account_type=AccountType.CHECKING,
            category=TransactionCategory.LOAN_PAYMENT,
            source_statement="test.pdf",
        ))
        
        aggregates = service.compute_monthly_aggregates(ledger, 2024)
        
        # Should have aggregates for all categories (except UNCATEGORIZED)
        categories = set(a.category for a in aggregates)
        assert TransactionCategory.UTILITIES in categories
        assert TransactionCategory.LOAN_PAYMENT in categories
        assert TransactionCategory.UNCATEGORIZED not in categories
    
    def test_compute_yearly_total(self):
        """Test computing yearly total for a category."""
        service = AggregationService()
        ledger = Ledger()
        
        # Add multiple entries for UTILITIES
        for month in range(1, 13):
            ledger.add_entry(LedgerEntry(
                transaction_id=f"util_{month}",
                date=date(2024, month, 15),
                description=f"Utility {month}",
                amount=Decimal("100.00"),
                account_type=AccountType.CREDIT_CARD,
                category=TransactionCategory.UTILITIES,
                source_statement="test.pdf",
            ))
        
        total = service.compute_yearly_total(ledger, 2024, TransactionCategory.UTILITIES)
        
        assert total == Decimal("1200.00")  # 12 months * $100
    
    def test_compute_aggregates_empty_ledger(self):
        """Test computing aggregates for empty ledger."""
        service = AggregationService()
        ledger = Ledger()
        
        aggregates = service.compute_monthly_aggregates(ledger, 2024)
        
        # Should still return aggregates (all zeros)
        assert len(aggregates) > 0
        
        # All totals should be zero
        for agg in aggregates:
            assert agg.total == Decimal("0")
            assert agg.running_total == Decimal("0")
