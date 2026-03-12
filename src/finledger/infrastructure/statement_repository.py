"""Statement repository implementation using ccparse and chkparse."""

import logging
from pathlib import Path
from typing import List

from ccparse import TDStatementParser
from chkparse import parse as parse_checking

from ..domain.exceptions import StatementIngestionError
from ..domain.repositories import StatementRepository

logger = logging.getLogger(__name__)


class StatementRepositoryImpl(StatementRepository):
    """Concrete implementation of StatementRepository using ccparse and chkparse."""
    
    def __init__(self):
        """Initialize parsers."""
        self.cc_parser = TDStatementParser()
    
    def load_credit_card_statements(self, directory: Path) -> List[any]:
        """
        Load all credit card statements from directory using ccparse.
        
        Args:
            directory: Path to directory containing CC statement PDFs
            
        Returns:
            List of parsed credit card statements
            
        Raises:
            StatementIngestionError: If directory doesn't exist or parsing fails
        """
        if not directory.exists():
            raise StatementIngestionError(f"Directory not found: {directory}")
        
        if not directory.is_dir():
            raise StatementIngestionError(f"Not a directory: {directory}")
        
        statements = []
        pdf_files = sorted(directory.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {directory}")
            return statements
        
        logger.info(f"Found {len(pdf_files)} PDF files in {directory}")
        
        for pdf in pdf_files:
            try:
                logger.debug(f"Parsing credit card statement: {pdf.name}")
                stmt = self.cc_parser.parse(str(pdf))
                
                # Attach filename for auditability
                stmt.filename = pdf.name
                statements.append(stmt)
                
                logger.info(f"✓ Parsed {pdf.name}: {len(stmt.transactions)} transactions")
                
            except Exception as e:
                logger.error(f"✗ Failed to parse {pdf.name}: {e}")
                # Continue processing other files
                continue
        
        logger.info(f"Successfully loaded {len(statements)} credit card statements")
        return statements
    
    def load_checking_statements(self, directory: Path) -> List[any]:
        """
        Load all checking statements from directory using chkparse.
        
        Args:
            directory: Path to directory containing checking statement PDFs
            
        Returns:
            List of parsed checking statements
            
        Raises:
            StatementIngestionError: If directory doesn't exist or parsing fails
        """
        if not directory.exists():
            raise StatementIngestionError(f"Directory not found: {directory}")
        
        if not directory.is_dir():
            raise StatementIngestionError(f"Not a directory: {directory}")
        
        statements = []
        pdf_files = sorted(directory.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {directory}")
            return statements
        
        logger.info(f"Found {len(pdf_files)} PDF files in {directory}")
        
        for pdf in pdf_files:
            try:
                logger.debug(f"Parsing checking statement: {pdf.name}")
                stmt = parse_checking(str(pdf))
                
                # Attach filename for auditability
                stmt.filename = pdf.name
                statements.append(stmt)
                
                logger.info(f"✓ Parsed {pdf.name}: {len(stmt.transactions)} transactions")
                
            except Exception as e:
                logger.error(f"✗ Failed to parse {pdf.name}: {e}")
                # Continue processing other files
                continue
        
        logger.info(f"Successfully loaded {len(statements)} checking statements")
        return statements
