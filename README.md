# finledger

Financial ledger system that ingests credit card and checking account statements, transforms them into a unified ledger, and syncs to Google Sheets for accountant review.

## What It Does

finledger automates the tedious process of consolidating financial statements from multiple sources:

1. **Ingests** PDF statements from TD credit cards and checking accounts
2. **Transforms** transactions into a normalized ledger format
3. **Categorizes** expenses automatically using configurable rules
4. **Aggregates** monthly totals by category
5. **Syncs** to Google Sheets for easy review and sharing with accountants

Built with Domain-Driven Design principles for maintainability and extensibility.

---

## Installation

```bash
cd finledger
uv sync
```

Requires Python 3.11+.

---

## Configuration

### 1. Copy the template

```bash
cp config.yaml.template config.yaml
```

### 2. Edit config.yaml

```yaml
statements:
  credit_card_dir: "/path/to/creditcard/statements"
  checking_dir: "/path/to/checking/statements"

google_sheets:
  spreadsheet_id: "your-spreadsheet-id-from-url"
  summary_sheet_name: "Monthly Summary"
  detail_sheet_name: "Transaction Detail"
  credentials_file: "client_secret.json"
  token_file: "token.json"
  scopes:
    - "https://www.googleapis.com/auth/spreadsheets"

category_mapping:
  UTILITIES:
    - "PROVIDENCE WATER"
    - "NARRAGANSETT BAY"
    - "PPL RHODE ISLAND"
  LOAN_PAYMENT:
    - "TD Bank.*LOAN PAYMENT"
  MUNICIPAL_FEES:
    - "CITY OF PROVIDEN"
  OFFICE_SUPPLIES:
    - "STAPLES"
  INSURANCE:
    - "INSURANCE"
  RENT:
    - "RENT"
  PAYROLL:
    - "PAYROLL"
    - "SALARY"

processing:
  year: 2024
  skip_validation: false
  dry_run: false
```

### 3. Set up Google Sheets credentials

1. Create a Google Cloud project
2. Enable Google Sheets API
3. Create OAuth 2.0 credentials
4. Download as `client_secret.json`
5. Place in project root

---

## Usage

### Validate Configuration

Check that your config is valid before processing:

```bash
uv run finledger validate
```

### View Configuration

Display current configuration settings:

```bash
uv run finledger info
```

### Ingest Statements

Process statements and display summary:

```bash
# Basic usage (uses paths from config.yaml)
uv run finledger ingest \
  --cc-dir /path/to/creditcard/statements \
  --checking-dir /path/to/checking/statements

# Preview with rich terminal tables (no Google Sheets sync)
uv run finledger ingest \
  --cc-dir /path/to/creditcard/statements \
  --checking-dir /path/to/checking/statements \
  --preview

# Override year from config
uv run finledger ingest \
  --cc-dir /path/to/creditcard/statements \
  --checking-dir /path/to/checking/statements \
  --year 2024

# Dry run (preview without syncing)
uv run finledger ingest \
  --cc-dir /path/to/creditcard/statements \
  --checking-dir /path/to/checking/statements \
  --dry-run

# Use custom config file
uv run finledger ingest \
  --cc-dir /path/to/creditcard/statements \
  --checking-dir /path/to/checking/statements \
  --config my-config.yaml
```

### Example Output

```
============================================================
INGESTING STATEMENTS
============================================================

📄 Loading credit card statements from: /path/to/creditcard
✓ Processed 12 CC statements, 245 transactions

📄 Loading checking statements from: /path/to/checking
✓ Processed 12 checking statements, 189 transactions

📊 SUMMARY
   Total statements: 24
   Total transactions: 434
   Credit card: 245
   Checking: 189

📋 CATEGORY BREAKDOWN
   UTILITIES: 36
   LOAN_PAYMENT: 12
   MUNICIPAL_FEES: 24
   OFFICE_SUPPLIES: 18
   UNCATEGORIZED: 344

============================================================
LEDGER SUMMARY FOR 2024
============================================================

UTILITIES
------------------------------------------------------------
  Jan: $450.00
  Feb: $475.00
  Mar: $460.00
  TOTAL: $1,385.00

LOAN_PAYMENT
------------------------------------------------------------
  Jan: $2,000.00
  Feb: $2,000.00
  Mar: $2,000.00
  TOTAL: $6,000.00
```

---

## Use Cases

### Preview Data Before Syncing

```bash
# View data in beautiful terminal tables without touching Google Sheets
uv run finledger ingest \
  --cc-dir ~/Statements/creditcard \
  --checking-dir ~/Statements/checking \
  --preview
```

### Monthly Bookkeeping

```bash
# Process current month's statements
uv run finledger ingest \
  --cc-dir ~/Statements/creditcard \
  --checking-dir ~/Statements/checking \
  --year 2024
```

### Year-End Review

```bash
# Process entire year
uv run finledger ingest \
  --cc-dir ~/Statements/2024/creditcard \
  --checking-dir ~/Statements/2024/checking \
  --year 2024
```

### Testing New Categories

```bash
# Dry run to test category mappings
uv run finledger ingest \
  --cc-dir ~/Statements/creditcard \
  --checking-dir ~/Statements/checking \
  --dry-run
```

### Multiple Configurations

```bash
# Use different config for different businesses
uv run finledger ingest \
  --cc-dir ~/Business1/statements/cc \
  --checking-dir ~/Business1/statements/checking \
  --config business1-config.yaml

uv run finledger ingest \
  --cc-dir ~/Business2/statements/cc \
  --checking-dir ~/Business2/statements/checking \
  --config business2-config.yaml
```

---

## Running Tests

### Run all tests

```bash
uv run pytest tests/ -v
```

### Run specific test types

```bash
# Unit tests only
uv run pytest tests/unit/ -v

# Integration tests only
uv run pytest tests/integration/ -v
```

### Run with coverage

```bash
uv run pytest tests/ --cov=finledger --cov-report=html
```

### Run specific test file

```bash
uv run pytest tests/unit/test_models.py -v
```

### Run tests matching pattern

```bash
uv run pytest tests/ -k "test_ledger" -v
```

---

## Features

- **Multi-source ingestion** - Parses TD credit card (via ccparse) and checking statements (via chkparse)
- **Unified ledger** - Normalizes transactions from multiple accounts into single view
- **Automatic categorization** - Maps transactions to expense categories via configurable regex rules
- **Monthly aggregates** - Computes monthly totals with running balances
- **Google Sheets sync** - Upserts data to spreadsheet for accountant review
- **Idempotent** - Safe to run multiple times without duplicates
- **Auditable** - Tracks source statement for every transaction
- **Flexible configuration** - YAML-based config with override options

---

## Project Structure

```
finledger/
├── src/finledger/
│   ├── application/        # Use cases
│   ├── domain/            # Business logic
│   ├── infrastructure/    # External integrations
│   └── cli.py            # Command-line interface
├── tests/
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── fixtures/         # Test data
├── docs/                 # Documentation
├── config.yaml.template  # Configuration template
└── pyproject.toml       # Project metadata
```

---

## License

MIT
