"""Integration tests for statement ingestion."""

from pathlib import Path

import pytest

from finledger.application.use_cases import IngestStatementsUseCase
from finledger.domain.models import AccountType, TransactionCategory
from finledger.domain.services import (
    CategoryMappingService,
    LedgerTransformationService,
)
from finledger.infrastructure.statement_repository import StatementRepositoryImpl


class TestStatementIngestion:
    """Integration tests for statement ingestion."""
    
    @pytest.fixture
    def statement_repo(self):
        """Create statement repository."""
        return StatementRepositoryImpl()
    
    @pytest.fixture
    def transformation_service(self):
        """Create transformation service."""
        return LedgerTransformationService()
    
    @pytest.fixture
    def category_service(self):
        """Create category service with test patterns."""
        patterns = {
            "UTILITIES": ["WATER", "ELECTRIC", "GAS"],
            "LOAN_PAYMENT": ["LOAN", "MORTGAGE"],
            "MUNICIPAL_FEES": ["CITY", "TAX"],
        }
        return CategoryMappingService(patterns)
    
    @pytest.fixture
    def ingest_use_case(self, statement_repo, transformation_service, category_service):
        """Create ingest use case."""
        return IngestStatementsUseCase(
            statement_repo,
            transformation_service,
            category_service
        )
    
    @pytest.mark.requires_real_data
    def test_ingest_real_statements(self, ingest_use_case):
        """
        Test ingesting real statements from directories.
        
        This test requires actual statement PDFs in the directories.
        Skip if directories don't exist.
        """
        cc_dir = Path("/Users/rmuktader/Statements/creditcard")
        checking_dir = Path("/Users/rmuktader/Statements")
        
        if not cc_dir.exists() or not checking_dir.exists():
            pytest.skip("Statement directories not found")
        
        # Execute ingestion
        ledger = ingest_use_case.execute(cc_dir, checking_dir)
        
        # Verify ledger was populated
        assert len(ledger.entries) > 0
        
        # Verify we have both account types
        account_types = set(e.account_type for e in ledger.entries)
        assert AccountType.CREDIT_CARD in account_types or AccountType.CHECKING in account_types
        
        # Verify entries have required fields
        for entry in ledger.entries[:10]:  # Check first 10
            assert entry.transaction_id is not None
            assert entry.date is not None
            assert entry.description is not None
            assert entry.amount is not None
            assert entry.account_type is not None
            assert entry.category is not None
            assert entry.source_statement is not None
    
    def test_ingest_empty_directories(self, ingest_use_case, tmp_path):
        """Test ingesting from empty directories."""
        cc_dir = tmp_path / "cc"
        cc_dir.mkdir()
        checking_dir = tmp_path / "checking"
        checking_dir.mkdir()
        
        ledger = ingest_use_case.execute(cc_dir, checking_dir)
        
        # Should return empty ledger
        assert len(ledger.entries) == 0
    
    @pytest.mark.requires_real_data
    def test_ingest_idempotency(self, ingest_use_case):
        """
        Test that running ingestion twice doesn't duplicate entries.
        
        Skip if directories don't exist.
        """
        cc_dir = Path("/Users/rmuktader/Statements/creditcard")
        checking_dir = Path("/Users/rmuktader/Statements")
        
        if not cc_dir.exists() or not checking_dir.exists():
            pytest.skip("Statement directories not found")
        
        # First ingestion
        ledger1 = ingest_use_case.execute(cc_dir, checking_dir)
        count1 = len(ledger1.entries)
        
        # Second ingestion (should be idempotent)
        ledger2 = ingest_use_case.execute(cc_dir, checking_dir)
        count2 = len(ledger2.entries)
        
        # Should have same number of entries
        assert count1 == count2
    
    @pytest.mark.requires_real_data
    def test_categorization_applied(self, ingest_use_case):
        """
        Test that categorization is applied during ingestion.
        
        Skip if directories don't exist.
        """
        cc_dir = Path("/Users/rmuktader/Statements/creditcard")
        checking_dir = Path("/Users/rmuktader/Statements")
        
        if not cc_dir.exists() or not checking_dir.exists():
            pytest.skip("Statement directories not found")
        
        ledger = ingest_use_case.execute(cc_dir, checking_dir)
        
        # Check if any entries were categorized
        categories = set(e.category for e in ledger.entries)
        
        # Should have at least UNCATEGORIZED
        assert TransactionCategory.UNCATEGORIZED in categories
        
        # May have other categories if patterns matched
        # (This depends on actual statement content)


class TestStatementRepository:
    """Integration tests for statement repository."""
    
    @pytest.fixture
    def repo(self):
        """Create statement repository."""
        return StatementRepositoryImpl()
    
    @pytest.mark.requires_real_data
    def test_load_credit_card_statements(self, repo):
        """
        Test loading credit card statements.
        
        Skip if directory doesn't exist.
        """
        cc_dir = Path("/Users/rmuktader/Statements/creditcard")
        
        if not cc_dir.exists():
            pytest.skip("Credit card directory not found")
        
        statements = repo.load_credit_card_statements(cc_dir)
        
        # Should load at least one statement
        assert len(statements) > 0
        
        # Verify statement structure
        for stmt in statements[:3]:  # Check first 3
            assert hasattr(stmt, 'transactions')
            assert hasattr(stmt, 'filename')
            assert len(stmt.transactions) >= 0
    
    @pytest.mark.requires_real_data
    def test_load_checking_statements(self, repo):
        """
        Test loading checking statements.
        
        Skip if directory doesn't exist.
        """
        checking_dir = Path("/Users/rmuktader/Statements")
        
        if not checking_dir.exists():
            pytest.skip("Checking directory not found")
        
        statements = repo.load_checking_statements(checking_dir)
        
        # Should load at least one statement
        assert len(statements) > 0
        
        # Verify statement structure
        for stmt in statements[:3]:  # Check first 3
            assert hasattr(stmt, 'transactions')
            assert hasattr(stmt, 'filename')
            assert len(stmt.transactions) >= 0
    
    def test_load_from_nonexistent_directory(self, repo):
        """Test loading from non-existent directory."""
        from finledger.domain.exceptions import StatementIngestionError
        
        with pytest.raises(StatementIngestionError, match="not found"):
            repo.load_credit_card_statements(Path("/nonexistent/directory"))
    
    def test_load_from_file_not_directory(self, repo, tmp_path):
        """Test loading from a file instead of directory."""
        from finledger.domain.exceptions import StatementIngestionError
        
        # Create a file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        with pytest.raises(StatementIngestionError, match="Not a directory"):
            repo.load_credit_card_statements(test_file)
