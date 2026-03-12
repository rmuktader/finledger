"""Integration tests using mock data (no real PDFs required)."""

from pathlib import Path

import pytest

from finledger.application.use_cases import (
    GenerateMonthlyAggregatesUseCase,
    IngestStatementsUseCase,
)
from finledger.domain.models import AccountType, TransactionCategory
from finledger.domain.services import (
    AggregationService,
    CategoryMappingService,
    LedgerTransformationService,
)


class TestIngestWithMockData:
    """Test ingestion with mock data (no real PDFs needed)."""
    
    def test_ingest_mock_statements(self, mock_statement_repository):
        """Test ingesting mock statements."""
        transformation_service = LedgerTransformationService()
        category_service = CategoryMappingService({
            "UTILITIES": ["WATER", "ELECTRIC"],
            "LOAN_PAYMENT": ["LOAN"],
        })
        
        use_case = IngestStatementsUseCase(
            mock_statement_repository,
            transformation_service,
            category_service
        )
        
        # Execute with dummy paths (not used by mock)
        ledger = use_case.execute(Path("/dummy/cc"), Path("/dummy/checking"))
        
        # Verify ledger was populated
        assert len(ledger.entries) == 4  # 2 CC + 2 checking
        
        # Verify both account types present
        account_types = set(e.account_type for e in ledger.entries)
        assert AccountType.CREDIT_CARD in account_types
        assert AccountType.CHECKING in account_types
    
    def test_categorization_with_mock_data(self, mock_statement_repository):
        """Test that categorization works with mock data."""
        transformation_service = LedgerTransformationService()
        category_service = CategoryMappingService({
            "UTILITIES": ["WATER", "ELECTRIC"],
            "LOAN_PAYMENT": ["LOAN"],
        })
        
        use_case = IngestStatementsUseCase(
            mock_statement_repository,
            transformation_service,
            category_service
        )
        
        ledger = use_case.execute(Path("/dummy/cc"), Path("/dummy/checking"))
        
        # Check categorization
        categories = set(e.category for e in ledger.entries)
        assert TransactionCategory.UTILITIES in categories
    
    def test_end_to_end_with_mock_data(self, mock_statement_repository):
        """Test complete workflow with mock data."""
        transformation_service = LedgerTransformationService()
        category_service = CategoryMappingService({
            "UTILITIES": ["WATER", "ELECTRIC"],
        })
        aggregation_service = AggregationService()
        
        # Ingest
        ingest_uc = IngestStatementsUseCase(
            mock_statement_repository,
            transformation_service,
            category_service
        )
        ledger = ingest_uc.execute(Path("/dummy/cc"), Path("/dummy/checking"))
        
        assert len(ledger.entries) > 0
        
        # Generate aggregates
        aggregate_uc = GenerateMonthlyAggregatesUseCase(aggregation_service)
        aggregates = aggregate_uc.execute(ledger, 2024)
        
        assert len(aggregates) > 0
        
        # Verify aggregates structure
        for agg in aggregates:
            assert agg.year == 2024
            assert 1 <= agg.month <= 12
            assert agg.total is not None
            assert agg.running_total is not None


class TestWithRealData:
    """Tests that require real PDF statements (marked for optional execution)."""
    
    @pytest.mark.requires_real_data
    def test_ingest_real_statements(self):
        """
        Test with real statements (optional - skipped by default).
        
        To run: pytest -m requires_real_data
        """
        from finledger.infrastructure.statement_repository import StatementRepositoryImpl
        
        cc_dir = Path("/Users/rmuktader/Statements/creditcard")
        checking_dir = Path("/Users/rmuktader/Statements")
        
        if not cc_dir.exists() or not checking_dir.exists():
            pytest.skip("Real statement directories not found")
        
        repo = StatementRepositoryImpl()
        transformation_service = LedgerTransformationService()
        category_service = CategoryMappingService({
            "UTILITIES": ["WATER", "ELECTRIC"],
        })
        
        use_case = IngestStatementsUseCase(
            repo,
            transformation_service,
            category_service
        )
        
        ledger = use_case.execute(cc_dir, checking_dir)
        assert len(ledger.entries) > 0
