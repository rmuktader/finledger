"""CLI interface for the financial ledger system."""

import logging
import sys
from pathlib import Path

import click

from .application.preview_service import PreviewService
from .application.use_cases import (
    DisplayLedgerSummaryUseCase,
    GenerateMonthlyAggregatesUseCase,
    IngestStatementsUseCase,
)
from .domain.services import (
    AggregationService,
    CategoryMappingService,
    LedgerTransformationService,
)
from .infrastructure.config_service import load_config, validate_config
from .infrastructure.statement_repository import StatementRepositoryImpl

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="1.0.0")
def main():
    """
    Financial Ledger Management System
    
    Ingest credit card and checking account statements,
    transform to unified ledger, and sync to Google Sheets.
    """
    pass


@main.command()
@click.option(
    '--cc-dir',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    required=True,
    help='Directory containing credit card statement PDFs'
)
@click.option(
    '--checking-dir',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    required=True,
    help='Directory containing checking statement PDFs'
)
@click.option(
    '--config',
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    default='config.yaml',
    help='Path to configuration file (default: config.yaml)'
)
@click.option(
    '--year',
    type=int,
    help='Year to process (overrides config)'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Preview without syncing to Google Sheets'
)
@click.option(
    '--preview',
    is_flag=True,
    help='Display data in rich terminal tables instead of syncing'
)
def ingest(cc_dir, checking_dir, config, year, dry_run, preview):
    """
    Ingest statements from directories and display summary.
    
    Example:
        finledger ingest --cc-dir /path/to/cc --checking-dir /path/to/checking
    """
    try:
        # Load configuration
        click.echo("Loading configuration...")
        cfg = load_config(config)
        
        # Override year if provided
        if year:
            cfg.processing.year = year
        
        click.echo(f"Processing year: {cfg.processing.year}\n")
        
        # Initialize repositories and services
        statement_repo = StatementRepositoryImpl()
        transformation_service = LedgerTransformationService()
        category_service = CategoryMappingService(cfg.category_mapping)
        aggregation_service = AggregationService()
        
        # Execute use case: Ingest statements
        ingest_uc = IngestStatementsUseCase(
            statement_repo,
            transformation_service,
            category_service
        )
        
        ledger = ingest_uc.execute(cc_dir, checking_dir)
        
        # Display summary
        summary_uc = DisplayLedgerSummaryUseCase()
        summary_uc.execute(ledger, cfg.processing.year)
        
        # Generate aggregates
        aggregate_uc = GenerateMonthlyAggregatesUseCase(aggregation_service)
        aggregates = aggregate_uc.execute(ledger, cfg.processing.year)
        
        # Display in rich tables if preview flag is set
        if preview:
            preview_service = PreviewService()
            preview_service.display_category_breakdown(ledger, cfg.processing.year)
            preview_service.display_monthly_summary(ledger, cfg.processing.year)
            preview_service.display_transaction_detail(ledger, cfg.processing.year, limit=50)
            
            click.echo("\n" + "=" * 60)
            click.echo("PREVIEW MODE - No changes made to Google Sheets")
            click.echo("=" * 60)
        elif dry_run:
            click.echo("\n" + "=" * 60)
            click.echo("DRY RUN - No changes made to Google Sheets")
            click.echo("=" * 60)
        else:
            click.echo("\n" + "=" * 60)
            click.echo("✓ Ingestion complete!")
            click.echo("=" * 60)
            click.echo("\nNext steps:")
            click.echo("  1. Review the summary above")
            click.echo("  2. Run 'finledger sync' to upload to Google Sheets")
        
    except Exception as e:
        click.echo(f"\n❌ Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    '--config',
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    default='config.yaml',
    help='Path to configuration file'
)
def validate(config):
    """
    Validate configuration and test connections.
    
    Example:
        finledger validate
    """
    try:
        click.echo("Validating configuration...")
        cfg = load_config(config)
        validate_config(cfg)
        
        click.echo("\n✓ Configuration is valid")
        click.echo(f"\nSettings:")
        click.echo(f"  Credit card dir: {cfg.statements.credit_card_dir}")
        click.echo(f"  Checking dir: {cfg.statements.checking_dir}")
        click.echo(f"  Processing year: {cfg.processing.year}")
        click.echo(f"  Categories: {len(cfg.category_mapping)}")
        
    except Exception as e:
        click.echo(f"\n❌ Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    '--config',
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    default='config.yaml',
    help='Path to configuration file'
)
def info(config):
    """
    Display configuration information.
    
    Example:
        finledger info
    """
    try:
        cfg = load_config(config)
        
        click.echo("\n" + "=" * 60)
        click.echo("CONFIGURATION")
        click.echo("=" * 60)
        
        click.echo("\n📁 Statement Directories:")
        click.echo(f"  Credit Card: {cfg.statements.credit_card_dir}")
        click.echo(f"  Checking:    {cfg.statements.checking_dir}")
        
        click.echo("\n📊 Google Sheets:")
        click.echo(f"  Spreadsheet ID: {cfg.google_sheets.spreadsheet_id}")
        click.echo(f"  Summary Sheet:  {cfg.google_sheets.summary_sheet_name}")
        click.echo(f"  Detail Sheet:   {cfg.google_sheets.detail_sheet_name}")
        
        click.echo("\n📋 Category Mapping:")
        for category, patterns in cfg.category_mapping.items():
            click.echo(f"  {category}:")
            for pattern in patterns[:3]:  # Show first 3 patterns
                click.echo(f"    - {pattern}")
            if len(patterns) > 3:
                click.echo(f"    ... and {len(patterns) - 3} more")
        
        click.echo("\n⚙️  Processing:")
        click.echo(f"  Year: {cfg.processing.year}")
        click.echo(f"  Skip validation: {cfg.processing.skip_validation}")
        click.echo(f"  Dry run: {cfg.processing.dry_run}")
        
    except Exception as e:
        click.echo(f"\n❌ Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
