"""Unit tests for configuration service."""

import tempfile
from pathlib import Path

import pytest

from finledger.domain.exceptions import ConfigurationError
from finledger.infrastructure.config_service import load_config, validate_config


class TestConfigService:
    """Test configuration service."""
    
    def test_load_valid_config(self, tmp_path):
        """Test loading valid configuration."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
statements:
  credit_card_dir: "/tmp/cc"
  checking_dir: "/tmp/checking"

google_sheets:
  spreadsheet_id: "test_id"
  summary_sheet_name: "Summary"
  detail_sheet_name: "Detail"
  credentials_file: "creds.json"
  token_file: "token.json"
  scopes:
    - "https://www.googleapis.com/auth/spreadsheets"

category_mapping:
  UTILITIES:
    - "WATER"
    - "ELECTRIC"

processing:
  year: 2024
  skip_validation: false
  dry_run: false
""")
        
        config = load_config(str(config_file))
        
        assert config.statements.credit_card_dir == "/tmp/cc"
        assert config.statements.checking_dir == "/tmp/checking"
        assert config.google_sheets.spreadsheet_id == "test_id"
        assert config.processing.year == 2024
        assert "UTILITIES" in config.category_mapping
    
    def test_load_config_file_not_found(self):
        """Test loading non-existent config file."""
        with pytest.raises(ConfigurationError, match="not found"):
            load_config("nonexistent.yaml")
    
    def test_load_config_empty_file(self, tmp_path):
        """Test loading empty config file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("")
        
        with pytest.raises(ConfigurationError, match="empty"):
            load_config(str(config_file))
    
    def test_load_config_missing_section(self, tmp_path):
        """Test loading config with missing required section."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
statements:
  credit_card_dir: "/tmp/cc"
  checking_dir: "/tmp/checking"
""")
        
        with pytest.raises(ConfigurationError, match="Missing required sections"):
            load_config(str(config_file))
    
    def test_load_config_invalid_yaml(self, tmp_path):
        """Test loading config with invalid YAML syntax."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
statements:
  credit_card_dir: "/tmp/cc"
  invalid yaml syntax here: [
""")
        
        with pytest.raises(ConfigurationError, match="Invalid YAML"):
            load_config(str(config_file))
    
    def test_validate_config_invalid_year(self, tmp_path):
        """Test validating config with invalid year."""
        # Create directories
        cc_dir = tmp_path / "cc"
        cc_dir.mkdir()
        chk_dir = tmp_path / "checking"
        chk_dir.mkdir()
        creds_file = tmp_path / "creds.json"
        creds_file.write_text("{}")
        
        config_file = tmp_path / "config.yaml"
        config_file.write_text(f"""
statements:
  credit_card_dir: "{cc_dir}"
  checking_dir: "{chk_dir}"

google_sheets:
  spreadsheet_id: "test_id"
  summary_sheet_name: "Summary"
  detail_sheet_name: "Detail"
  credentials_file: "{creds_file}"
  token_file: "token.json"
  scopes:
    - "https://www.googleapis.com/auth/spreadsheets"

category_mapping:
  UTILITIES:
    - "WATER"

processing:
  year: 1999
  skip_validation: false
  dry_run: false
""")
        
        config = load_config(str(config_file))
        
        with pytest.raises(ConfigurationError, match="Invalid year"):
            validate_config(config)
    
    def test_validate_config_directory_not_found(self, tmp_path):
        """Test validating config with non-existent directory."""
        creds_file = tmp_path / "creds.json"
        creds_file.write_text("{}")
        
        config_file = tmp_path / "config.yaml"
        config_file.write_text(f"""
statements:
  credit_card_dir: "/nonexistent/cc"
  checking_dir: "/nonexistent/checking"

google_sheets:
  spreadsheet_id: "test_id"
  summary_sheet_name: "Summary"
  detail_sheet_name: "Detail"
  credentials_file: "{creds_file}"
  token_file: "token.json"
  scopes:
    - "https://www.googleapis.com/auth/spreadsheets"

category_mapping:
  UTILITIES:
    - "WATER"

processing:
  year: 2024
  skip_validation: false
  dry_run: false
""")
        
        config = load_config(str(config_file))
        
        with pytest.raises(ConfigurationError, match="directory not found"):
            validate_config(config)
    
    def test_validate_config_credentials_not_found(self, tmp_path):
        """Test validating config with non-existent credentials file."""
        cc_dir = tmp_path / "cc"
        cc_dir.mkdir()
        chk_dir = tmp_path / "checking"
        chk_dir.mkdir()
        
        config_file = tmp_path / "config.yaml"
        config_file.write_text(f"""
statements:
  credit_card_dir: "{cc_dir}"
  checking_dir: "{chk_dir}"

google_sheets:
  spreadsheet_id: "test_id"
  summary_sheet_name: "Summary"
  detail_sheet_name: "Detail"
  credentials_file: "nonexistent.json"
  token_file: "token.json"
  scopes:
    - "https://www.googleapis.com/auth/spreadsheets"

category_mapping:
  UTILITIES:
    - "WATER"

processing:
  year: 2024
  skip_validation: false
  dry_run: false
""")
        
        config = load_config(str(config_file))
        
        with pytest.raises(ConfigurationError, match="Credentials file not found"):
            validate_config(config)
