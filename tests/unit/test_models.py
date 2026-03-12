"""Unit tests for domain models."""

from datetime import date
from decimal import Decimal

import pytest

from finledger.domain.models import (
    AccountType,
    Ledger,
    LedgerEntry,
    MonthlyAggregate,
    TransactionCategory,
)


class TestLedgerEntry:
    """Test LedgerEntry entity."""
    
    def test_create_ledger_entry(self):
        """Test creating a ledger entry."""
        entry = LedgerEntry(
            transaction_id="2024-01-15_TEST_100.00_CREDIT_CARD",
            date=date(2024, 1, 15),
            description="Test Transaction",
            amount=Decimal("100.00"),
            account_type=AccountType.CREDIT_CARD,
            category=TransactionCategory.UTILITIES,
            source_statement="test_statement.pdf",
        )
        
        assert entry.transaction_id == "2024-01-15_TEST_100.00_CREDIT_CARD"
        assert entry.date == date(2024, 1, 15)
        assert entry.description == "Test Transaction"
        assert entry.amount == Decimal("100.00")
        assert entry.account_type == AccountType.CREDIT_CARD
        assert entry.category == TransactionCategory.UTILITIES
        assert entry.source_statement == "test_statement.pdf"
    
    def test_ledger_entry_is_immutable(self):
        """Test that LedgerEntry is immutable (frozen)."""
        entry = LedgerEntry(
            transaction_id="test_id",
            date=date(2024, 1, 15),
            description="Test",
            amount=Decimal("100.00"),
            account_type=AccountType.CREDIT_CARD,
            category=TransactionCategory.UTILITIES,
            source_statement="test.pdf",
        )
        
        with pytest.raises(AttributeError):
            entry.amount = Decimal("200.00")


class TestMonthlyAggregate:
    """Test MonthlyAggregate value object."""
    
    def test_create_monthly_aggregate(self):
        """Test creating a monthly aggregate."""
        aggregate = MonthlyAggregate(
            year=2024,
            month=1,
            category=TransactionCategory.UTILITIES,
            total=Decimal("450.00"),
            running_total=Decimal("450.00"),
        )
        
        assert aggregate.year == 2024
        assert aggregate.month == 1
        assert aggregate.category == TransactionCategory.UTILITIES
        assert aggregate.total == Decimal("450.00")
        assert aggregate.running_total == Decimal("450.00")
    
    def test_monthly_aggregate_is_immutable(self):
        """Test that MonthlyAggregate is immutable (frozen)."""
        aggregate = MonthlyAggregate(
            year=2024,
            month=1,
            category=TransactionCategory.UTILITIES,
            total=Decimal("450.00"),
            running_total=Decimal("450.00"),
        )
        
        with pytest.raises(AttributeError):
            aggregate.total = Decimal("500.00")


class TestLedger:
    """Test Ledger aggregate root."""
    
    def test_create_empty_ledger(self):
        """Test creating an empty ledger."""
        ledger = Ledger()
        assert len(ledger.entries) == 0
    
    def test_add_entry(self):
        """Test adding an entry to ledger."""
        ledger = Ledger()
        entry = LedgerEntry(
            transaction_id="test_id_1",
            date=date(2024, 1, 15),
            description="Test",
            amount=Decimal("100.00"),
            account_type=AccountType.CREDIT_CARD,
            category=TransactionCategory.UTILITIES,
            source_statement="test.pdf",
        )
        
        ledger.add_entry(entry)
        assert len(ledger.entries) == 1
        assert ledger.entries[0] == entry
    
    def test_add_entry_is_idempotent(self):
        """Test that adding same entry twice doesn't duplicate."""
        ledger = Ledger()
        entry = LedgerEntry(
            transaction_id="test_id_1",
            date=date(2024, 1, 15),
            description="Test",
            amount=Decimal("100.00"),
            account_type=AccountType.CREDIT_CARD,
            category=TransactionCategory.UTILITIES,
            source_statement="test.pdf",
        )
        
        ledger.add_entry(entry)
        ledger.add_entry(entry)  # Add same entry again
        
        assert len(ledger.entries) == 1  # Should only have one entry
    
    def test_get_entries_by_month(self):
        """Test filtering entries by month."""
        ledger = Ledger()
        
        # Add entries for different months
        entry1 = LedgerEntry(
            transaction_id="jan_1",
            date=date(2024, 1, 15),
            description="January",
            amount=Decimal("100.00"),
            account_type=AccountType.CREDIT_CARD,
            category=TransactionCategory.UTILITIES,
            source_statement="test.pdf",
        )
        entry2 = LedgerEntry(
            transaction_id="feb_1",
            date=date(2024, 2, 15),
            description="February",
            amount=Decimal("200.00"),
            account_type=AccountType.CREDIT_CARD,
            category=TransactionCategory.UTILITIES,
            source_statement="test.pdf",
        )
        
        ledger.add_entry(entry1)
        ledger.add_entry(entry2)
        
        jan_entries = ledger.get_entries_by_month(2024, 1)
        assert len(jan_entries) == 1
        assert jan_entries[0].description == "January"
        
        feb_entries = ledger.get_entries_by_month(2024, 2)
        assert len(feb_entries) == 1
        assert feb_entries[0].description == "February"
    
    def test_get_entries_by_category(self):
        """Test filtering entries by category."""
        ledger = Ledger()
        
        entry1 = LedgerEntry(
            transaction_id="util_1",
            date=date(2024, 1, 15),
            description="Utility",
            amount=Decimal("100.00"),
            account_type=AccountType.CREDIT_CARD,
            category=TransactionCategory.UTILITIES,
            source_statement="test.pdf",
        )
        entry2 = LedgerEntry(
            transaction_id="loan_1",
            date=date(2024, 1, 15),
            description="Loan",
            amount=Decimal("2000.00"),
            account_type=AccountType.CHECKING,
            category=TransactionCategory.LOAN_PAYMENT,
            source_statement="test.pdf",
        )
        
        ledger.add_entry(entry1)
        ledger.add_entry(entry2)
        
        util_entries = ledger.get_entries_by_category(TransactionCategory.UTILITIES)
        assert len(util_entries) == 1
        assert util_entries[0].description == "Utility"
        
        loan_entries = ledger.get_entries_by_category(TransactionCategory.LOAN_PAYMENT)
        assert len(loan_entries) == 1
        assert loan_entries[0].description == "Loan"
    
    def test_get_entries_by_year(self):
        """Test filtering entries by year."""
        ledger = Ledger()
        
        entry1 = LedgerEntry(
            transaction_id="2024_1",
            date=date(2024, 1, 15),
            description="2024",
            amount=Decimal("100.00"),
            account_type=AccountType.CREDIT_CARD,
            category=TransactionCategory.UTILITIES,
            source_statement="test.pdf",
        )
        entry2 = LedgerEntry(
            transaction_id="2025_1",
            date=date(2025, 1, 15),
            description="2025",
            amount=Decimal("200.00"),
            account_type=AccountType.CREDIT_CARD,
            category=TransactionCategory.UTILITIES,
            source_statement="test.pdf",
        )
        
        ledger.add_entry(entry1)
        ledger.add_entry(entry2)
        
        entries_2024 = ledger.get_entries_by_year(2024)
        assert len(entries_2024) == 1
        assert entries_2024[0].description == "2024"
        
        entries_2025 = ledger.get_entries_by_year(2025)
        assert len(entries_2025) == 1
        assert entries_2025[0].description == "2025"
    
    def test_get_total_by_category(self):
        """Test calculating total by category."""
        ledger = Ledger()
        
        entry1 = LedgerEntry(
            transaction_id="util_1",
            date=date(2024, 1, 15),
            description="Utility 1",
            amount=Decimal("100.00"),
            account_type=AccountType.CREDIT_CARD,
            category=TransactionCategory.UTILITIES,
            source_statement="test.pdf",
        )
        entry2 = LedgerEntry(
            transaction_id="util_2",
            date=date(2024, 2, 15),
            description="Utility 2",
            amount=Decimal("150.00"),
            account_type=AccountType.CREDIT_CARD,
            category=TransactionCategory.UTILITIES,
            source_statement="test.pdf",
        )
        
        ledger.add_entry(entry1)
        ledger.add_entry(entry2)
        
        total = ledger.get_total_by_category(TransactionCategory.UTILITIES, 2024)
        assert total == Decimal("250.00")
