"""Generate mock PDF statements for testing.

This script creates sanitized, fake PDF statements that mimic the structure
of real TD statements but contain no real financial data.
"""

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

# Mock data generator
def generate_mock_cc_statement():
    """Generate mock credit card statement data."""
    from dataclasses import dataclass
    
    @dataclass
    class MockCCTransaction:
        activity_date: date
        post_date: date
        reference_number: str
        description: str
        amount: Decimal
    
    @dataclass
    class MockCCStatement:
        entity_name: str = "TEST COMPANY LLC"
        primary_cardholder: str = "TEST USER"
        account_suffix: str = "1234"
        billing_period_start: date = date(2024, 1, 1)
        billing_period_end: date = date(2024, 1, 31)
        filename: str = "test_cc_statement.pdf"
        
        @property
        def transactions(self):
            return [
                MockCCTransaction(
                    activity_date=date(2024, 1, 5),
                    post_date=date(2024, 1, 6),
                    reference_number="REF001",
                    description="TEST WATER COMPANY",
                    amount=Decimal("125.50")
                ),
                MockCCTransaction(
                    activity_date=date(2024, 1, 15),
                    post_date=date(2024, 1, 16),
                    reference_number="REF002",
                    description="TEST ELECTRIC UTILITY",
                    amount=Decimal("200.00")
                ),
                MockCCTransaction(
                    activity_date=date(2024, 1, 20),
                    post_date=date(2024, 1, 21),
                    reference_number="REF003",
                    description="TEST OFFICE SUPPLIES",
                    amount=Decimal("75.25")
                ),
            ]
    
    return MockCCStatement()


def generate_mock_checking_statement():
    """Generate mock checking statement data."""
    from dataclasses import dataclass
    
    @dataclass
    class MockCheckingTransaction:
        posting_date: date
        description: str
        amount: Decimal
        transaction_type: str
    
    @dataclass
    class MockCheckingStatement:
        entity_name: str = "TEST COMPANY LLC"
        account_number: str = "123-4567890"
        account_suffix: str = "7890"
        statement_period_start: date = date(2024, 1, 1)
        statement_period_end: date = date(2024, 1, 31)
        filename: str = "test_checking_statement.pdf"
        
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
                MockCheckingTransaction(
                    posting_date=date(2024, 1, 15),
                    description="TD Bank LOAN PAYMENT",
                    amount=Decimal("2000.00"),
                    transaction_type="ELECTRONIC_PAYMENT"
                ),
                MockCheckingTransaction(
                    posting_date=date(2024, 1, 20),
                    description="TEST CITY TAX",
                    amount=Decimal("350.00"),
                    transaction_type="ELECTRONIC_PAYMENT"
                ),
            ]
    
    return MockCheckingStatement()


if __name__ == "__main__":
    print("Mock statement generators created")
    print("\nMock CC Statement:")
    cc = generate_mock_cc_statement()
    print(f"  Entity: {cc.entity_name}")
    print(f"  Transactions: {len(cc.transactions)}")
    
    print("\nMock Checking Statement:")
    chk = generate_mock_checking_statement()
    print(f"  Entity: {chk.entity_name}")
    print(f"  Transactions: {len(chk.transactions)}")
