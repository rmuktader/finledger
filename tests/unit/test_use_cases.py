"""Unit tests for application use cases."""

from datetime import date
from decimal import Decimal

import pytest

from finledger.application.use_cases import (
    DisplayLedgerSummaryUseCase,
    GenerateMonthlyAggregatesUseCase,
)
from finledger.domain.models import (
    AccountType,
    Ledger,
    LedgerEntry,
    TransactionCategory,
)
from finledger.domain.services import AggregationService


class TestGenerateMonthlyAggregatesUseCase:
    """Test GenerateMonthlyAggregatesUseCase."""
    
    def test_execute(self, sample_ledger):
        """Test executing monthly aggregates use case."""
        aggregation_service = AggregationService()
        use_case = GenerateMonthlyAggregatesUseCase(aggregation_service)
        
        aggregates = use_case.execute(sample_ledger, 2024)
        
        # Should return aggregates
        assert len(aggregates) > 0
        
        # All should be for 2024
        for agg in aggregates:
            assert agg.year == 2024


class TestDisplayLedgerSummaryUseCase:
    """Test DisplayLedgerSummaryUseCase."""
    
    def test_execute_with_entries(self, sample_ledger, caplog):
        """Test displaying summary with entries."""
        import logging
        caplog.set_level(logging.INFO)
        
        use_case = DisplayLedgerSummaryUseCase()
        
        # Execute (logs to console)
        use_case.execute(sample_ledger, 2024)
        
        # Verify logging occurred
        assert "LEDGER SUMMARY FOR 2024" in caplog.text
        assert "UTILITIES" in caplog.text or "LOAN_PAYMENT" in caplog.text
        assert "GRAND TOTAL" in caplog.text
    
    def test_execute_empty_ledger(self, caplog):
        """Test displaying summary with empty ledger."""
        import logging
        caplog.set_level(logging.INFO)
        
        use_case = DisplayLedgerSummaryUseCase()
        ledger = Ledger()
        
        use_case.execute(ledger, 2024)
        
        # Should log "No transactions found"
        assert "No transactions found for 2024" in caplog.text
    
    def test_execute_no_entries_for_year(self, caplog):
        """Test displaying summary when no entries for specified year."""
        import logging
        caplog.set_level(logging.INFO)
        
        use_case = DisplayLedgerSummaryUseCase()
        ledger = Ledger()
        
        # Add entry for different year
        ledger.add_entry(LedgerEntry(
            transaction_id="test_2023",
            date=date(2023, 1, 15),
            description="2023 Transaction",
            amount=Decimal("100.00"),
            account_type=AccountType.CREDIT_CARD,
            category=TransactionCategory.UTILITIES,
            source_statement="test.pdf",
        ))
        
        # Request summary for 2024
        use_case.execute(ledger, 2024)
        
        # Should log "No transactions found"
        assert "No transactions found for 2024" in caplog.text
    
    def test_execute_displays_categories(self, caplog):
        """Test that summary displays all categories."""
        import logging
        caplog.set_level(logging.INFO)
        
        use_case = DisplayLedgerSummaryUseCase()
        ledger = Ledger()
        
        # Add entries for multiple categories
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
        
        use_case.execute(ledger, 2024)
        
        # Should display both categories
        assert "UTILITIES" in caplog.text
        assert "LOAN_PAYMENT" in caplog.text
    
    def test_execute_displays_monthly_breakdown(self, caplog):
        """Test that summary displays monthly breakdown."""
        import logging
        caplog.set_level(logging.INFO)
        
        use_case = DisplayLedgerSummaryUseCase()
        ledger = Ledger()
        
        # Add entries for different months
        ledger.add_entry(LedgerEntry(
            transaction_id="jan_1",
            date=date(2024, 1, 15),
            description="January",
            amount=Decimal("100.00"),
            account_type=AccountType.CREDIT_CARD,
            category=TransactionCategory.UTILITIES,
            source_statement="test.pdf",
        ))
        
        ledger.add_entry(LedgerEntry(
            transaction_id="feb_1",
            date=date(2024, 2, 15),
            description="February",
            amount=Decimal("150.00"),
            account_type=AccountType.CREDIT_CARD,
            category=TransactionCategory.UTILITIES,
            source_statement="test.pdf",
        ))
        
        use_case.execute(ledger, 2024)
        
        # Should display month names
        assert "Jan" in caplog.text
        assert "Feb" in caplog.text
        
        # Should display amounts
        assert "100.00" in caplog.text
        assert "150.00" in caplog.text
    
    def test_execute_calculates_totals(self, caplog):
        """Test that summary calculates category and grand totals."""
        import logging
        caplog.set_level(logging.INFO)
        
        use_case = DisplayLedgerSummaryUseCase()
        ledger = Ledger()
        
        # Add multiple entries
        ledger.add_entry(LedgerEntry(
            transaction_id="util_1",
            date=date(2024, 1, 15),
            description="Utility 1",
            amount=Decimal("100.00"),
            account_type=AccountType.CREDIT_CARD,
            category=TransactionCategory.UTILITIES,
            source_statement="test.pdf",
        ))
        
        ledger.add_entry(LedgerEntry(
            transaction_id="util_2",
            date=date(2024, 2, 15),
            description="Utility 2",
            amount=Decimal("150.00"),
            account_type=AccountType.CREDIT_CARD,
            category=TransactionCategory.UTILITIES,
            source_statement="test.pdf",
        ))
        
        use_case.execute(ledger, 2024)
        
        # Should display TOTAL for category (100 + 150 = 250)
        assert "TOTAL" in caplog.text
        assert "250.00" in caplog.text
        
        # Should display GRAND TOTAL
        assert "GRAND TOTAL" in caplog.text
