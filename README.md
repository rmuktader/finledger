# finledger

Financial ledger system that ingests credit card and checking account statements, transforms them into a unified ledger, and syncs to Google Sheets for accountant review.

---

## Features

- **Multi-source ingestion** - Parses TD credit card (via ccparse) and checking statements (via chkparse)
- **Unified ledger** - Normalizes transactions from multiple accounts into single view
- **Automatic categorization** - Maps transactions to expense categories via configurable rules
- **Monthly aggregates** - Computes monthly totals with running balances
- **Google Sheets sync** - Upserts data to spreadsheet for accountant review
- **Idempotent** - Safe to run multiple times without duplicates
- **Auditable** - Tracks source statement for every transaction

---

## Installation

```bash
cd finledger
uv sync
```

Requires Python 3.11+.

---

## Quick Start

### 1. Configure

Create `config.yaml`:

```yaml
statements:
  credit_card_dir: "/path/to/creditcard/statements"
  checking_dir: "/path/to/checking/statements"

google_sheets:
  spreadsheet_id: "your-spreadsheet-id"
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
  LOAN_PAYMENT:
    - "TD Bank.*LOAN"
  MUNICIPAL_FEES:
    - "CITY OF PROVIDEN"

processing:
  year: 2024
```

### 2. Run

```bash
# Sync statements to Google Sheets
uv run finledger sync

# Dry run (preview without syncing)
uv run finledger sync --dry-run

# Validate configuration
uv run finledger validate
```

---

## Architecture

Built with Domain-Driven Design principles:

```
┌─────────────────────────────────────────┐
│         CLI (main.py)                   │
├─────────────────────────────────────────┤
│    Application Layer (Use Cases)        │
│  - IngestStatements                     │
│  - GenerateAggregates                   │
│  - SyncToSheets                         │
├─────────────────────────────────────────┤
│    Domain Layer                         │
│  - Ledger (Aggregate Root)              │
│  - LedgerEntry (Entity)                 │
│  - MonthlyAggregate (Value Object)      │
├─────────────────────────────────────────┤
│    Infrastructure Layer                 │
│  - StatementRepository (ccparse/chkparse)│
│  - GoogleSheetsRepository (gspread)     │
└─────────────────────────────────────────┘
```

See [docs/technical-design-doc.md](docs/technical-design-doc.md) for full architecture.

---

## Google Sheets Layout

### Monthly Summary Sheet

```
     A          B      C      D    ...    M      N
1  Category    Jan    Feb    Mar  ...   Dec   Total
2  UTILITIES   450    475    460  ...   480   5500
3  LOAN_PMT   2000   2000   2000  ...  2000  24000
```

### Transaction Detail Sheet

```
     A           B                    C        D          E            F
1  Date    Description            Amount   Account    Category     Source
2  2024-01-05  PROVIDENCE WATER    125.50   CC      UTILITIES    stmt_jan.pdf
3  2024-01-10  TD LOAN PAYMENT    2000.00   CHECKING LOAN_PMT    chk_jan.pdf
```

---

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=finledger
```

---

## License

MIT
