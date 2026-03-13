"""Configuration service for loading and validating config files."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import yaml

from ..domain.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


@dataclass
class StatementsConfig:
    """Configuration for statement directories."""
    credit_card_dir: str
    checking_dir: str


@dataclass
class GoogleSheetsConfig:
    """Configuration for Google Sheets integration."""
    spreadsheet_id: str
    summary_sheet_name: str
    detail_sheet_name: str
    credentials_file: str
    token_file: str
    scopes: List[str]


@dataclass
class ProcessingConfig:
    """Configuration for processing options."""
    year: int
    skip_validation: bool = False
    dry_run: bool = False


@dataclass
class Config:
    """Main configuration object."""
    statements: StatementsConfig
    google_sheets: GoogleSheetsConfig
    category_mapping: Dict[str, List[str]]
    processing: ProcessingConfig


def load_config(config_path: str = "config.yaml") -> Config:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config.yaml file
        
    Returns:
        Config object with validated configuration
        
    Raises:
        ConfigurationError: If config file is invalid or missing
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise ConfigurationError(f"Configuration file not found: {config_path}")
    
    try:
        data = _parse_config_file(config_file)
        
        config = Config(
            statements=StatementsConfig(**data['statements']),
            google_sheets=GoogleSheetsConfig(**data['google_sheets']),
            category_mapping=data['category_mapping'],
            processing=ProcessingConfig(**data['processing']),
        )
        
        logger.info(f"✓ Configuration loaded from {config_path}")
        return config
        
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML syntax: {e}") from e
    except TypeError as e:
        raise ConfigurationError(f"Invalid configuration structure: {e}") from e
    except Exception as e:
        raise ConfigurationError(f"Failed to load configuration: {e}") from e


def _parse_config_file(config_file: Path) -> dict:
    """Parse YAML config file and validate required sections are present."""
    with open(config_file) as f:
        if not (data := yaml.safe_load(f)):
            raise ConfigurationError("Configuration file is empty")
    
    required_sections = ['statements', 'google_sheets', 'category_mapping', 'processing']
    if missing := [s for s in required_sections if s not in data]:
        raise ConfigurationError(f"Missing required sections: {missing}")
    
    return data


def validate_config(config: Config) -> None:
    """
    Validate configuration values.
    
    Args:
        config: Config object to validate
        
    Raises:
        ConfigurationError: If configuration is invalid
    """
    # Validate directories exist
    cc_dir = Path(config.statements.credit_card_dir)
    if not cc_dir.exists():
        raise ConfigurationError(f"Credit card directory not found: {cc_dir}")
    
    chk_dir = Path(config.statements.checking_dir)
    if not chk_dir.exists():
        raise ConfigurationError(f"Checking directory not found: {chk_dir}")
    
    # Validate year
    if config.processing.year < 2000 or config.processing.year > 2100:
        raise ConfigurationError(f"Invalid year: {config.processing.year}")
    
    # Validate Google Sheets credentials file exists
    creds_file = Path(config.google_sheets.credentials_file)
    if not creds_file.exists():
        raise ConfigurationError(f"Credentials file not found: {creds_file}")
    
    logger.info("✓ Configuration validated")
