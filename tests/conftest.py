"""Pytest configuration and fixtures."""

import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_ledger_entry():
    """Create a sample ledger entry for testing."""
    from datetime import date
    from decimal import Decimal
    
    from finledger.domain.models import (
        AccountType,
        LedgerEntry,
        TransactionCategory,
    )
    
    return LedgerEntry(
        transaction_id="test_id_123",
        date=date(2024, 1, 15),
        description="Test Transaction",
        amount=Decimal("100.00"),
        account_type=AccountType.CREDIT_CARD,
        category=TransactionCategory.UTILITIES,
        source_statement="test_statement.pdf",
    )


@pytest.fixture
def sample_ledger():
    """Create a sample ledger with multiple entries."""
    from datetime import date
    from decimal import Decimal
    
    from finledger.domain.models import (
        AccountType,
        Ledger,
        LedgerEntry,
        TransactionCategory,
    )
    
    ledger = Ledger()
    
    # Add some sample entries
    for month in range(1, 4):  # Jan, Feb, Mar
        ledger.add_entry(LedgerEntry(
            transaction_id=f"util_{month}",
            date=date(2024, month, 15),
            description=f"Utility {month}",
            amount=Decimal("100.00"),
            account_type=AccountType.CREDIT_CARD,
            category=TransactionCategory.UTILITIES,
            source_statement="test.pdf",
        ))
        
        ledger.add_entry(LedgerEntry(
            transaction_id=f"loan_{month}",
            date=date(2024, month, 1),
            description=f"Loan {month}",
            amount=Decimal("2000.00"),
            account_type=AccountType.CHECKING,
            category=TransactionCategory.LOAN_PAYMENT,
            source_statement="test.pdf",
        ))
    
    return ledger


@pytest.fixture
def mock_cc_statement():
    """Create a mock credit card statement."""
    from datetime import date
    from decimal import Decimal
    from dataclasses import dataclass
    
    @dataclass
    class MockCCTransaction:
        post_date: date
        description: str
        amount: Decimal
    
    @dataclass
    class MockCCStatement:
        filename: str = "test_cc.pdf"
        
        @property
        def transactions(self):
            return [
                MockCCTransaction(
                    post_date=date(2024, 1, 5),
                    description="TEST WATER COMPANY",
                    amount=Decimal("125.50")
                ),
                MockCCTransaction(
                    post_date=date(2024, 1, 15),
                    description="TEST ELECTRIC UTILITY",
                    amount=Decimal("200.00")
                ),
            ]
    
    return MockCCStatement()


@pytest.fixture
def mock_checking_statement():
    """Create a mock checking statement."""
    from datetime import date
    from decimal import Decimal
    from dataclasses import dataclass
    
    @dataclass
    class MockCheckingTransaction:
        posting_date: date
        description: str
        amount: Decimal
        transaction_type: str
    
    @dataclass
    class MockCheckingStatement:
        filename: str = "test_checking.pdf"
        
        @property
        def transactions(self):
            return [
                MockCheckingTransaction(
                    posting_date=date(2024, 1, 5),
                    description="TEST WATER PAYMENT",
                    amount=Decimal("125.50"),
                    transaction_type="ELECTRONIC_PAYMENT"
                ),
                MockCheckingTransaction(
                    posting_date=date(2024, 1, 10),
                    description="TEST DEPOSIT",
                    amount=Decimal("5000.00"),
                    transaction_type="ELECTRONIC_DEPOSIT"
                ),
            ]
    
    return MockCheckingStatement()


@pytest.fixture
def mock_statement_repository(mock_cc_statement, mock_checking_statement):
    """Create a mock statement repository for testing."""
    from finledger.domain.repositories import StatementRepository
    
    class MockStatementRepository(StatementRepository):
        def __init__(self, cc_statements, checking_statements):
            self.cc_statements = cc_statements
            self.checking_statements = checking_statements
        
        def load_credit_card_statements(self, directory):
            return self.cc_statements
        
        def load_checking_statements(self, directory):
            return self.checking_statements
    
    return MockStatementRepository(
        [mock_cc_statement],
        [mock_checking_statement]
    )


@pytest.fixture
def fixtures_dir():
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires real data)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_real_data: mark test as requiring real statement PDFs"
    )
