"""Service for previewing ledger data in rich terminal tables."""

from collections import defaultdict
from decimal import Decimal
from typing import List

from rich.console import Console
from rich.table import Table

from ..domain.models import Ledger, MonthlyAggregate


class PreviewService:
    """Service for displaying ledger data in terminal tables."""
    
    def __init__(self):
        self.console = Console()
    
    def display_monthly_summary(self, ledger: Ledger, year: int) -> None:
        """
        Display monthly summary table similar to Google Sheets format.
        
        Args:
            ledger: Ledger containing all entries
            year: Year to display
        """
        # Group by category and month
        monthly_by_category = defaultdict(lambda: defaultdict(Decimal))
        
        year_entries = ledger.get_entries_by_year(year)
        
        for entry in year_entries:
            monthly_by_category[entry.category][entry.date.month] += entry.amount
        
        # Create table
        table = Table(title=f"Monthly Summary - {year}", show_header=True, header_style="bold magenta")
        
        # Add columns
        table.add_column("Category", style="cyan", no_wrap=True)
        for month in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]:
            table.add_column(month, justify="right", style="green")
        table.add_column("Total", justify="right", style="bold yellow")
        
        # Add rows
        for category in sorted(monthly_by_category.keys(), key=lambda c: c.value):
            monthly_totals = monthly_by_category[category]
            yearly_total = Decimal("0")
            
            row = [category.value]
            for month in range(1, 13):
                total = monthly_totals.get(month, Decimal("0"))
                yearly_total += total
                row.append(f"${total:,.2f}" if total != 0 else "-")
            
            row.append(f"${yearly_total:,.2f}")
            table.add_row(*row)
        
        # Grand total row
        grand_total = sum(e.amount for e in year_entries)
        self.console.print()
        self.console.print(table)
        self.console.print(f"\n[bold]Grand Total: [yellow]${grand_total:,.2f}[/yellow][/bold]")
    
    def display_transaction_detail(self, ledger: Ledger, year: int, limit: int = 100) -> None:
        """
        Display transaction detail table.
        
        Args:
            ledger: Ledger containing all entries
            year: Year to display
            limit: Maximum number of transactions to display
        """
        year_entries = sorted(ledger.get_entries_by_year(year), key=lambda e: e.date)
        
        table = Table(title=f"Transaction Detail - {year}", show_header=True, header_style="bold magenta")
        
        table.add_column("Date", style="cyan")
        table.add_column("Description", style="white", max_width=40)
        table.add_column("Amount", justify="right", style="green")
        table.add_column("Account", style="blue")
        table.add_column("Category", style="yellow")
        table.add_column("Source", style="dim", max_width=30)
        
        displayed = 0
        for entry in year_entries:
            if displayed >= limit:
                break
            
            table.add_row(
                entry.date.strftime("%Y-%m-%d"),
                entry.description[:40],
                f"${entry.amount:,.2f}",
                entry.account_type.value,
                entry.category.value,
                entry.source_statement
            )
            displayed += 1
        
        self.console.print()
        self.console.print(table)
        
        if len(year_entries) > limit:
            self.console.print(f"\n[dim]Showing {limit} of {len(year_entries)} transactions[/dim]")
    
    def display_category_breakdown(self, ledger: Ledger, year: int) -> None:
        """
        Display category breakdown with transaction counts and totals.
        
        Args:
            ledger: Ledger containing all entries
            year: Year to display
        """
        from collections import Counter
        
        year_entries = ledger.get_entries_by_year(year)
        
        # Count and sum by category
        category_counts = Counter(e.category for e in year_entries)
        category_totals = defaultdict(Decimal)
        
        for entry in year_entries:
            category_totals[entry.category] += entry.amount
        
        table = Table(title=f"Category Breakdown - {year}", show_header=True, header_style="bold magenta")
        
        table.add_column("Category", style="cyan")
        table.add_column("Count", justify="right", style="blue")
        table.add_column("Total", justify="right", style="green")
        table.add_column("Average", justify="right", style="yellow")
        
        for category, count in category_counts.most_common():
            total = category_totals[category]
            avg = total / count if count > 0 else Decimal("0")
            
            table.add_row(
                category.value,
                str(count),
                f"${total:,.2f}",
                f"${avg:,.2f}"
            )
        
        self.console.print()
        self.console.print(table)
