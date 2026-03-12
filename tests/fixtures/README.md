# Test Fixtures

This directory contains test fixtures for the finledger test suite.

---

## Approach: Mock Data Instead of Real Statements

### Why Mock Data?

1. **Security** - No real financial data in version control
2. **Portability** - Tests run on any machine without setup
3. **Speed** - Mock data is faster than parsing real PDFs
4. **Consistency** - Same test data across all environments
5. **CI/CD** - Works in automated pipelines without credentials

### Industry Standard Pattern

This follows the **Test Fixture Pattern** from industry best practices:

```
tests/
├── fixtures/           # Test data
│   ├── creditcard/    # Mock CC statements (if needed)
│   ├── checking/      # Mock checking statements (if needed)
│   └── generate_fixtures.py  # Mock data generators
├── unit/              # Fast tests with mocks
└── integration/       # Tests with mock repositories
```

---

## How It Works

### 1. Mock Statements (In-Memory)

Instead of real PDFs, we use Python dataclasses:

```python
@dataclass
class MockCCStatement:
    filename: str = "test_cc.pdf"
    
    @property
    def transactions(self):
        return [
            MockCCTransaction(
                post_date=date(2024, 1, 5),
                description="TEST WATER COMPANY",
                amount=Decimal("125.50")
            ),
        ]
```

### 2. Mock Repository

The `MockStatementRepository` returns mock data instead of parsing PDFs:

```python
class MockStatementRepository(StatementRepository):
    def load_credit_card_statements(self, directory):
        return [mock_cc_statement]  # Returns mock, not real PDF
    
    def load_checking_statements(self, directory):
        return [mock_checking_statement]
```

### 3. Pytest Fixtures

Fixtures in `conftest.py` provide mock data to all tests:

```python
@pytest.fixture
def mock_statement_repository():
    return MockStatementRepository(...)
```

---

## Test Categories

### Fast Tests (Default)

Run without any real data:

```bash
pytest tests/
```

Uses:
- Mock statements (in-memory)
- Mock repositories
- No file I/O

**Execution time:** < 1 second

### Optional Real Data Tests

Marked with `@pytest.mark.requires_real_data`:

```bash
pytest -m requires_real_data
```

Only runs if real statement directories exist. Skips gracefully otherwise.

---

## Benefits

### ✅ Security
- No sensitive financial data in repo
- No PII (Personally Identifiable Information)
- Safe to share publicly

### ✅ Portability
- Works on any developer machine
- No setup required
- No environment-specific paths

### ✅ CI/CD Ready
- Runs in GitHub Actions
- No credentials needed
- Fast execution

### ✅ Maintainability
- Easy to add new test cases
- Controlled test data
- Predictable results

---

## Adding New Test Data

### Option 1: In-Memory Mocks (Recommended)

Add to `conftest.py`:

```python
@pytest.fixture
def mock_multi_month_statement():
    @dataclass
    class MockStatement:
        filename: str = "test_multi_month.pdf"
        
        @property
        def transactions(self):
            return [
                # Add test transactions
            ]
    
    return MockStatement()
```

### Option 2: JSON Fixtures (For Complex Data)

Create `fixtures/sample_statement.json`:

```json
{
  "entity_name": "TEST COMPANY",
  "transactions": [
    {
      "date": "2024-01-05",
      "description": "TEST TRANSACTION",
      "amount": "100.00"
    }
  ]
}
```

Load in tests:

```python
import json

def load_fixture(name):
    with open(f"tests/fixtures/{name}.json") as f:
        return json.load(f)
```

---

## Real Data Testing (Optional)

For developers who want to test with real statements:

### Setup

1. Create local directory (not in repo):
   ```bash
   mkdir -p ~/test_statements/{creditcard,checking}
   ```

2. Copy sanitized statements (remove sensitive data)

3. Run with marker:
   ```bash
   pytest -m requires_real_data
   ```

### .gitignore

Real statements are excluded:

```gitignore
tests/fixtures/creditcard/*.pdf
tests/fixtures/checking/*.pdf
~/test_statements/
```

---

## Comparison: Mock vs Real Data

| Aspect | Mock Data | Real Data |
|---|---|---|
| **Speed** | < 1 second | ~4 minutes |
| **Security** | ✅ Safe | ⚠️ Sensitive |
| **Portability** | ✅ Any machine | ❌ Specific setup |
| **CI/CD** | ✅ Works | ❌ Requires secrets |
| **Maintenance** | ✅ Easy | ⚠️ Manual updates |
| **Coverage** | ✅ Controlled | ✅ Realistic |

---

## Best Practices

### ✅ DO

- Use mock data for unit and integration tests
- Keep mock data simple and focused
- Use realistic but fake values
- Document what each fixture represents

### ❌ DON'T

- Commit real financial statements
- Include PII in test data
- Hardcode real account numbers
- Use production credentials

---

## Example Test

```python
def test_with_mock_data(mock_statement_repository):
    """Test using mock data (fast, portable, secure)."""
    use_case = IngestStatementsUseCase(
        mock_statement_repository,
        transformation_service,
        category_service
    )
    
    # Dummy paths - not used by mock
    ledger = use_case.execute(Path("/dummy/cc"), Path("/dummy/checking"))
    
    assert len(ledger.entries) > 0
```

---

## References

- [Test Fixture Pattern](https://martinfowler.com/bliki/TestFixture.html)
- [Test Data Builders](https://www.natpryce.com/articles/000714.html)
- [Mocks Aren't Stubs](https://martinfowler.com/articles/mocksArentStubs.html)

---

## Summary

**Mock data is the industry standard for testing financial applications.**

Benefits:
- ✅ Secure (no real data)
- ✅ Portable (works anywhere)
- ✅ Fast (< 1 second)
- ✅ Maintainable (controlled data)
- ✅ CI/CD ready

Real data testing is optional and marked with `@pytest.mark.requires_real_data`.
