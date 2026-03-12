"""Integration tests for end-to-end workflow."""

from pathlib import Path

import pytest

from finledger.application.use_cases import (
    GenerateMonthlyAggregatesUseCase,
    IngestStatementsUseCase,
)
from finledger.domain.models import TransactionCategory
from finledger.domain.services import (
    AggregationService,
    CategoryMappingService,
    LedgerTransformationService,
)
from finledger.infrastructure.statement_repository import StatementRepositoryImpl


class TestEndToEndWorkflow:
    """Integration tests for complete workflow."""
    
    @pytest.fixture
    def services(self):
        """Create all required services."""
        return {
            'statement_repo': StatementRepositoryImpl(),
            'transformation': LedgerTransformationService(),
            'category': CategoryMappingService({
                "UTILITIES": ["WATER", "ELECTRIC", "GAS", "PPL"],
                "LOAN_PAYMENT": ["LOAN", "MORTGAGE", "TD Bank.*LOAN"],
                "MUNICIPAL_FEES": ["CITY", "TAX", "PROVIDEN"],
            }),
            'aggregation': AggregationService(),
        }
    
    @pytest.mark.requires_real_data
    def test_complete_workflow(self, services):
        """
        Test complete workflow: ingest → aggregate → display.
        
        Skip if directories don't exist.
        """
        cc_dir = Path("/Users/rmuktader/Statements/creditcard")
        checking_dir = Path("/Users/rmuktader/Statements")
        
        if not cc_dir.exists() or not checking_dir.exists():
            pytest.skip("Statement directories not found")
        
        # Step 1: Ingest statements
        ingest_uc = IngestStatementsUseCase(
            services['statement_repo'],
            services['transformation'],
            services['category']
        )
        ledger = ingest_uc.execute(cc_dir, checking_dir)
        
        assert len(ledger.entries) > 0
        
        # Step 2: Generate monthly aggregates
        aggregate_uc = GenerateMonthlyAggregatesUseCase(services['aggregation'])
        aggregates = aggregate_uc.execute(ledger, 2024)
        
        assert len(aggregates) > 0
        
        # Verify aggregates structure
        for agg in aggregates[:10]:  # Check first 10
            assert agg.year == 2024
            assert 1 <= agg.month <= 12
            assert agg.category != TransactionCategory.UNCATEGORIZED
            assert agg.total is not None
            assert agg.running_total is not None
        
        # Step 3: Verify running totals are cumulative
        # Group by category
        by_category = {}
        for agg in aggregates:
            if agg.category not in by_category:
                by_category[agg.category] = []
            by_category[agg.category].append(agg)
        
        # Check each category's running totals
        for category, aggs in by_category.items():
            sorted_aggs = sorted(aggs, key=lambda a: a.month)
            
            for i in range(1, len(sorted_aggs)):
                prev = sorted_aggs[i - 1]
                curr = sorted_aggs[i]
                
                # Running total should be previous running total + current month total
                expected = prev.running_total + curr.total
                assert curr.running_total == expected, \
                    f"Running total mismatch for {category} month {curr.month}"
    
    @pytest.mark.requires_real_data
    def test_workflow_with_filtering(self, services):
        """
        Test workflow with filtering by year.
        
        Skip if directories don't exist.
        """
        cc_dir = Path("/Users/rmuktader/Statements/creditcard")
        checking_dir = Path("/Users/rmuktader/Statements")
        
        if not cc_dir.exists() or not checking_dir.exists():
            pytest.skip("Statement directories not found")
        
        # Ingest all statements
        ingest_uc = IngestStatementsUseCase(
            services['statement_repo'],
            services['transformation'],
            services['category']
        )
        ledger = ingest_uc.execute(cc_dir, checking_dir)
        
        # Generate aggregates for 2024
        aggregate_uc = GenerateMonthlyAggregatesUseCase(services['aggregation'])
        aggregates_2024 = aggregate_uc.execute(ledger, 2024)
        
        # All aggregates should be for 2024
        for agg in aggregates_2024:
            assert agg.year == 2024
        
        # Generate aggregates for 2025
        aggregates_2025 = aggregate_uc.execute(ledger, 2025)
        
        # All aggregates should be for 2025
        for agg in aggregates_2025:
            assert agg.year == 2025
    
    @pytest.mark.requires_real_data
    def test_workflow_category_totals(self, services):
        """
        Test that category totals match sum of monthly totals.
        
        Skip if directories don't exist.
        """
        cc_dir = Path("/Users/rmuktader/Statements/creditcard")
        checking_dir = Path("/Users/rmuktader/Statements")
        
        if not cc_dir.exists() or not checking_dir.exists():
            pytest.skip("Statement directories not found")
        
        # Ingest and aggregate
        ingest_uc = IngestStatementsUseCase(
            services['statement_repo'],
            services['transformation'],
            services['category']
        )
        ledger = ingest_uc.execute(cc_dir, checking_dir)
        
        aggregate_uc = GenerateMonthlyAggregatesUseCase(services['aggregation'])
        aggregates = aggregate_uc.execute(ledger, 2024)
        
        # Group by category
        by_category = {}
        for agg in aggregates:
            if agg.category not in by_category:
                by_category[agg.category] = []
            by_category[agg.category].append(agg)
        
        # For each category, verify yearly total
        for category, aggs in by_category.items():
            # Sum of monthly totals
            monthly_sum = sum(a.total for a in aggs)
            
            # Last month's running total should equal sum of all monthly totals
            last_month = max(aggs, key=lambda a: a.month)
            assert last_month.running_total == monthly_sum, \
                f"Yearly total mismatch for {category}"
    
    @pytest.mark.requires_real_data
    def test_workflow_handles_multiple_years(self, services):
        """
        Test workflow with statements spanning multiple years.
        
        Skip if directories don't exist.
        """
        cc_dir = Path("/Users/rmuktader/Statements/creditcard")
        checking_dir = Path("/Users/rmuktader/Statements")
        
        if not cc_dir.exists() or not checking_dir.exists():
            pytest.skip("Statement directories not found")
        
        # Ingest all statements
        ingest_uc = IngestStatementsUseCase(
            services['statement_repo'],
            services['transformation'],
            services['category']
        )
        ledger = ingest_uc.execute(cc_dir, checking_dir)
        
        # Get unique years from ledger
        years = set(e.date.year for e in ledger.entries)
        
        if len(years) < 2:
            pytest.skip("Need statements from multiple years")
        
        # Generate aggregates for each year
        aggregate_uc = GenerateMonthlyAggregatesUseCase(services['aggregation'])
        
        for year in years:
            aggregates = aggregate_uc.execute(ledger, year)
            
            # All aggregates should be for the correct year
            for agg in aggregates:
                assert agg.year == year
            
            # Should have 12 months per category
            by_category = {}
            for agg in aggregates:
                if agg.category not in by_category:
                    by_category[agg.category] = []
                by_category[agg.category].append(agg)
            
            for category, aggs in by_category.items():
                assert len(aggs) == 12, f"Should have 12 months for {category} in {year}"
