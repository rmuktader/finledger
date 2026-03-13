"""Tests for preview service."""

from datetime import date
from decimal import Decimal
from io import StringIO

import pytest

from finledger.application.preview_service import PreviewService
from finledger.domain.models import (
    AccountType,
    Ledger,
    LedgerEntry,
    TransactionCategory,
)


def test_preview_service_displays_monthly_summary(sample_ledger, capsys):
    """Test that preview service displays monthly summary table."""
    preview_service = PreviewService()
    
    # Display monthly summary
    preview_service.display_monthly_summary(sample_ledger, 2024)
    
    # Capture output (Rich writes to stdout)
    captured = capsys.readouterr()
    
    # Verify table title appears
    assert "Monthly Summary - 2024" in captured.out
    
    # Verify categories appear
    assert "UTILITIES" in captured.out
    assert "LOAN_PAYMENT" in captured.out
    
    # Verify grand total appears
    assert "Grand Total" in captured.out


def test_preview_service_displays_transaction_detail(sample_ledger, capsys):
    """Test that preview service displays transaction detail table."""
    preview_service = PreviewService()
    
    # Display transaction detail
    preview_service.display_transaction_detail(sample_ledger, 2024, limit=10)
    
    captured = capsys.readouterr()
    
    # Verify table title appears
    assert "Transaction Detail - 2024" in captured.out
    
    # Verify column headers appear
    assert "Date" in captured.out
    assert "Description" in captured.out
    assert "Amount" in captured.out
    assert "Category" in captured.out


def test_preview_service_displays_category_breakdown(sample_ledger, capsys):
    """Test that preview service displays category breakdown table."""
    preview_service = PreviewService()
    
    # Display category breakdown
    preview_service.display_category_breakdown(sample_ledger, 2024)
    
    captured = capsys.readouterr()
    
    # Verify table title appears
    assert "Category Breakdown - 2024" in captured.out
    
    # Verify column headers appear
    assert "Category" in captured.out
    assert "Count" in captured.out
    assert "Total" in captured.out
    assert "Average" in captured.out


def test_preview_service_handles_empty_ledger(capsys):
    """Test that preview service handles empty ledger gracefully."""
    preview_service = PreviewService()
    empty_ledger = Ledger()
    
    # Should not raise exception
    preview_service.display_monthly_summary(empty_ledger, 2024)
    preview_service.display_transaction_detail(empty_ledger, 2024)
    preview_service.display_category_breakdown(empty_ledger, 2024)
    
    captured = capsys.readouterr()
    
    # Should still display table titles
    assert "Monthly Summary - 2024" in captured.out
    assert "Transaction Detail - 2024" in captured.out
    assert "Category Breakdown - 2024" in captured.out


def test_preview_service_limits_transaction_display(capsys):
    """Test that preview service respects transaction limit."""
    preview_service = PreviewService()
    
    # Create ledger with many entries
    ledger = Ledger()
    for i in range(100):
        ledger.add_entry(LedgerEntry(
            transaction_id=f"test_{i}",
            date=date(2024, 1, 1),
            description=f"Transaction {i}",
            amount=Decimal("100.00"),
            account_type=AccountType.CREDIT_CARD,
            category=TransactionCategory.UTILITIES,
            source_statement="test.pdf",
        ))
    
    # Display with limit of 10
    preview_service.display_transaction_detail(ledger, 2024, limit=10)
    
    captured = capsys.readouterr()
    
    # Should show limit message
    assert "Showing 10 of 100 transactions" in captured.out
