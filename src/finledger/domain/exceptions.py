"""Domain exceptions for the financial ledger system."""


class FinLedgerError(Exception):
    """Base exception for all finledger errors."""
    pass


class StatementIngestionError(FinLedgerError):
    """Raised when statement parsing fails."""
    pass


class CategoryMappingError(FinLedgerError):
    """Raised when category mapping fails."""
    pass


class AggregationError(FinLedgerError):
    """Raised when aggregation computation fails."""
    pass


class SheetSyncError(FinLedgerError):
    """Raised when Google Sheets sync fails."""
    pass


class ConfigurationError(FinLedgerError):
    """Raised when configuration is invalid."""
    pass
