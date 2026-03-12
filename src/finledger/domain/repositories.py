"""Repository interfaces for the domain layer (Dependency Inversion Principle)."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from .models import Ledger, LedgerEntry, MonthlyAggregate


class StatementRepository(ABC):
    """Abstract repository for loading financial statements."""
    
    @abstractmethod
    def load_credit_card_statements(self, directory: Path) -> List[any]:
        """
        Load all credit card statements from directory.
        
        Args:
            directory: Path to directory containing CC statement PDFs
            
        Returns:
            List of parsed credit card statements
            
        Raises:
            StatementIngestionError: If parsing fails
        """
        pass
    
    @abstractmethod
    def load_checking_statements(self, directory: Path) -> List[any]:
        """
        Load all checking statements from directory.
        
        Args:
            directory: Path to directory containing checking statement PDFs
            
        Returns:
            List of parsed checking statements
            
        Raises:
            StatementIngestionError: If parsing fails
        """
        pass


class LedgerRepository(ABC):
    """Abstract repository for persisting ledger data."""
    
    @abstractmethod
    def save(self, ledger: Ledger) -> None:
        """Persist ledger to storage."""
        pass
    
    @abstractmethod
    def load(self) -> Ledger:
        """Load ledger from storage."""
        pass


class SheetRepository(ABC):
    """Abstract repository for Google Sheets synchronization."""
    
    @abstractmethod
    def upsert_monthly_aggregates(self, aggregates: List[MonthlyAggregate]) -> None:
        """
        Upsert monthly aggregates to Google Sheets.
        
        Args:
            aggregates: List of monthly aggregates to sync
            
        Raises:
            SheetSyncError: If sync fails
        """
        pass
    
    @abstractmethod
    def upsert_transactions(self, entries: List[LedgerEntry]) -> None:
        """
        Upsert individual transactions to Google Sheets.
        
        Args:
            entries: List of ledger entries to sync
            
        Raises:
            SheetSyncError: If sync fails
        """
        pass
