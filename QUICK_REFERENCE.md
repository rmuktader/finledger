# finledger Quick Reference

## Installation

```bash
cd /Users/rmuktader/Worspace/personal/finledger
uv sync
```

## Commands

### Display Configuration
```bash
uv run python -m finledger.cli info
```

### Validate Configuration
```bash
uv run python -m finledger.cli validate
```

### Ingest Statements
```bash
uv run python -m finledger.cli ingest \
  --cc-dir /Users/rmuktader/Statements/creditcard \
  --checking-dir /Users/rmuktader/Statements \
  --dry-run
```

### Ingest for Specific Year
```bash
uv run python -m finledger.cli ingest \
  --cc-dir /Users/rmuktader/Statements/creditcard \
  --checking-dir /Users/rmuktader/Statements \
  --year 2024 \
  --dry-run
```

## Configuration

Edit `config.yaml`:

```yaml
statements:
  credit_card_dir: "/path/to/cc/statements"
  checking_dir: "/path/to/checking/statements"

category_mapping:
  UTILITIES:
    - "WATER"
    - "ELECTRIC"
  LOAN_PAYMENT:
    - "LOAN"
    - "MORTGAGE"

processing:
  year: 2024
```

## Project Structure

```
finledger/
├── src/finledger/
│   ├── domain/          # Business logic
│   ├── application/     # Use cases
│   ├── infrastructure/  # External integrations
│   └── cli.py          # CLI interface
├── config.yaml         # Configuration
└── pyproject.toml      # Dependencies
```

## Test Results

✅ **51 statements** processed  
✅ **459 transactions** ingested  
✅ **24 CC statements**  
✅ **27 checking statements**

## Next Steps

1. Add more category patterns to `config.yaml`
2. Implement Google Sheets sync
3. Run without `--dry-run` to sync to sheets
