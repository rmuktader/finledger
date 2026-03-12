"""Application layer use cases for the financial ledger system."""

import logging
from pathlib import Path
from typing import List

from ..domain.models import Ledger, MonthlyAggregate
from ..domain.repositories import StatementRepository
from ..domain.services import (
    AggregationService,
    CategoryMappingService,
    LedgerTransformationService,
)

logger = logging.getLogger(__name__)


class IngestStatementsUseCase:
    """Use case for ingesting statements from directories."""
    
    def __init__(
        self,
        statement_repo: StatementRepository,
        transformation_service: LedgerTransformationService,
        category_service: CategoryMappingService,
    ):
        """
        Initialize use case with dependencies.
        
        Args:
            statement_repo: Repository for loading statements
            transformation_service: Service for transforming transactions
            category_service: Service for categorizing transactions
        """
        self.statement_repo = statement_repo
        self.transformation_service = transformation_service
        self.category_service = category_service
    
    def execute(self, cc_dir: Path, checking_dir: Path) -> Ledger:
        """
        Ingest all statements and return unified ledger.
        
        Args:
            cc_dir: Directory containing credit card statement PDFs
            checking_dir: Directory containing checking statement PDFs
            
        Returns:
            Ledger containing all normalized and categorized transactions
        """
        logger.info("=" * 60)
        logger.info("INGESTING STATEMENTS")
        logger.info("=" * 60)
        
        ledger = Ledger()
        
        # Load and process credit card statements
        logger.info(f"\n📄 Loading credit card statements from: {cc_dir}")
        cc_statements = self.statement_repo.load_credit_card_statements(cc_dir)
        
        cc_count = 0
        for stmt in cc_statements:
            for txn in stmt.transactions:
                # Transform to ledger entry
                entry = self.transformation_service.from_cc_transaction(txn, stmt)
                
                # Categorize
                entry = self.category_service.categorize(entry)
                
                # Add to ledger (idempotent)
                ledger.add_entry(entry)
                cc_count += 1
        
        logger.info(f"✓ Processed {len(cc_statements)} CC statements, {cc_count} transactions")
        
        # Load and process checking statements
        logger.info(f"\n📄 Loading checking statements from: {checking_dir}")
        chk_statements = self.statement_repo.load_checking_statements(checking_dir)
        
        chk_count = 0
        for stmt in chk_statements:
            for txn in stmt.transactions:
                # Transform to ledger entry
                entry = self.transformation_service.from_checking_transaction(txn, stmt)
                
                # Categorize
                entry = self.category_service.categorize(entry)
                
                # Add to ledger (idempotent)
                ledger.add_entry(entry)
                chk_count += 1
        
        logger.info(f"✓ Processed {len(chk_statements)} checking statements, {chk_count} transactions")
        
        # Summary
        logger.info(f"\n📊 SUMMARY")
        logger.info(f"   Total statements: {len(cc_statements) + len(chk_statements)}")
        logger.info(f"   Total transactions: {len(ledger.entries)}")
        logger.info(f"   Credit card: {cc_count}")
        logger.info(f"   Checking: {chk_count}")
        
        # Category breakdown
        from collections import Counter
        category_counts = Counter(e.category for e in ledger.entries)
        logger.info(f"\n📋 CATEGORY BREAKDOWN")
        for category, count in category_counts.most_common():
            logger.info(f"   {category.value}: {count}")
        
        return ledger


class GenerateMonthlyAggregatesUseCase:
    """Use case for generating monthly aggregates."""
    
    def __init__(self, aggregation_service: AggregationService):
        """
        Initialize use case with dependencies.
        
        Args:
            aggregation_service: Service for computing aggregates
        """
        self.aggregation_service = aggregation_service
    
    def execute(self, ledger: Ledger, year: int) -> List[MonthlyAggregate]:
        """
        Generate monthly aggregates for a specific year.
        
        Args:
            ledger: Ledger containing all entries
            year: Year to compute aggregates for
            
        Returns:
            List of MonthlyAggregate objects
        """
        logger.info(f"\n📊 Generating monthly aggregates for {year}...")
        
        aggregates = self.aggregation_service.compute_monthly_aggregates(ledger, year)
        
        logger.info(f"✓ Generated {len(aggregates)} monthly aggregates")
        
        return aggregates


class DisplayLedgerSummaryUseCase:
    """Use case for displaying ledger summary."""
    
    def execute(self, ledger: Ledger, year: int) -> None:
        """
        Display summary of ledger for a specific year.
        
        Args:
            ledger: Ledger to summarize
            year: Year to summarize
        """
        from collections import defaultdict
        from decimal import Decimal
        
        logger.info(f"\n" + "=" * 60)
        logger.info(f"LEDGER SUMMARY FOR {year}")
        logger.info("=" * 60)
        
        # Get entries for the year
        year_entries = ledger.get_entries_by_year(year)
        
        if not year_entries:
            logger.info(f"No transactions found for {year}")
            return
        
        # Group by category and month
        monthly_by_category = defaultdict(lambda: defaultdict(Decimal))
        
        for entry in year_entries:
            monthly_by_category[entry.category][entry.date.month] += entry.amount
        
        # Display by category
        for category in sorted(monthly_by_category.keys(), key=lambda c: c.value):
            logger.info(f"\n{category.value}")
            logger.info("-" * 60)
            
            monthly_totals = monthly_by_category[category]
            yearly_total = Decimal("0")
            
            for month in range(1, 13):
                total = monthly_totals.get(month, Decimal("0"))
                yearly_total += total
                
                if total != 0:
                    month_name = [
                        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
                    ][month - 1]
                    logger.info(f"  {month_name}: ${total:,.2f}")
            
            logger.info(f"  {'TOTAL':>4}: ${yearly_total:,.2f}")
        
        # Grand total
        grand_total = sum(e.amount for e in year_entries)
        logger.info(f"\n{'=' * 60}")
        logger.info(f"GRAND TOTAL: ${grand_total:,.2f}")
        logger.info(f"{'=' * 60}")
