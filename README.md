# Personal Finance Tracker

A command-line application for tracking income and expenses, managing budgets, and exporting financial reports.

## Features

- Add, list, search, and delete transactions (income and expenses)
- Per-category monthly budget limits with overspend alerts
- Summary views: by category, by month, overall statistics
- Export in JSON (transactions, full reports)
- Persistent JSON storage — data survives between sessions
- Audit log of all mutating actions in `data/audit.log`

## Requirements

- Python 3.10 or higher
- No third-party packages required

## Running the app

```bash
# Clone or download the project, then:
cd finance-tracker-cli
python main.py
```

The app creates a `data/` directory automatically on first run.

## Project structure

```
finance_tracker/
├── main.py               # Entry point
├── cli/
│   └── menu.py           # All menus and user prompts
├── core/
│   ├── budget.py         # Budget limits and alerts
│   ├── tracker.py        # Central business logic
│   └── transaction.py    # Transaction dataclass
├── reports/
│   ├── analytics.py      # Summaries and generators
│   └── exporter.py       # CSV and JSON export
├── storage/
│   └── persistence.py    # Load/save JSON data
├── utils/
│   ├── decorators.py     # @log_action, @validate_input, @require_confirmation
│   ├── validators.py     # Regex-based input validation and lambdas
│   └── exceptions.py     # Custom exception hierarchy
├── data/                 # Auto-created — stores transaction.json, budgets.json, audit.log
├── tests/                # Unit tests for tracker and storage
|    └── test_regressions.py              
└── exports/              # Auto-created — stores exported files
```

## Usage guide

| Menu option | What it does |
|---|---|
| 0 — add income 
| 1 — add expense
| 2 — list transactions: both income and expense transactions, income only, exepse only, transactions based on the category
| 3 — search the transaction by the keyword in merchant name or note added to the transaction
| 4 — delete transaction by id
| 5 — category summary
| 6 — monthly summary
| 7 — overall statistics 
| 8 — Budget limits limits, set or update limit, remove limit or just list them all
| 9 - Export data (export transcsarions in JSON, or create a full report in JSON)
| x - Exit the program 

## Data format

Transactions are stored in `data/transaction.json`. Each record contains:

```json
{
  "id": "a1b2c3d4",
  "amount": 49.99,
  "category": "food",
  "merchant": "Biedronka",
  "date": "2024-03-15",
  "note": "Weekdgely groceries",
  "type": "expense"
}
```

## Notes

- The transaction type is constrained with Python's standard-library Literal type hint:
  Literal['income', 'expense']
- Dates must be in `YYYY-MM-DD` format
- Budget limits apply per calendar month
- The `exports/` directory is safe to clear at any time — it only contains generated reports

data about recent transactions can be loaded not only from instant session but as 
well from the previous sessions using transaction.json file 
in data module 


=======================================================
Package responsibilities
=======================================================

CLI
Responsible for the final look of the console-based interface.
menu.py
Contains all menus, user prompts, input loops, and display formatting. This is the only package the user directly interacts with. It reads input, formats output, and calls the appropriate Tracker methods. It has no knowledge of how data is stored or how business rules work.
All display constants (LINE, THIN, width) are defined at the top and reused across every menu function. Helper functions header(), success(), error(), and info() keep output consistent throughout. After every mutating action, menu.py calls persistence.save() to write the updated state to disk.

CORE
Contains the three classes that make up the business logic of the application.
transaction.py
The data model. Represents a single financial transaction using a Python dataclass. Fields: id (8-char UUID), amount, category, merchant, date, type (income or expense), and an optional note. The post_init method normalizes the merchant name and validates the category on every creation, whether from user input or loaded from JSON. Provides from_dict() to reconstruct a Transaction from stored data and to_dict() to serialize it back.
budget.py
Manages monthly spending limits. Stores a dictionary of category-to-limit pairs and exposes methods to set, remove, and check limits. The check() method raises BudgetExceededError if current spending in a category exceeds its limit. Provides from_dict() and to_dict() for JSON persistence. Uses None as the default for the limits parameter instead of an empty dict to avoid the mutable default argument problem.
tracker.py
The central class that coordinates everything. Holds all application state during runtime: a list of Transaction objects, a Budget instance, and a set of known categories. Exposes the full API used by the CLI: add_expense(), add_income(), delete_transaction(), set_budget(), search(), get_expenses(), get_income(), get_by_category(), totals_by_category(), net_balance(), budget_status(). add_expense() performs three checks before accepting a transaction: duplicate ID, budget limit, and available balance. Both add_expense() and add_income() are decorated with @log_action and @validate_input.

DATA
Auto-created on first run. Contains all persistent application state.
transaction.json
Stores the list of all transactions as a JSON array. Each record contains id, amount, category, merchant, date, note, and type. Overwritten on every save — not appended.
budgets.json
Stores budget limits as a flat JSON object mapping category names to their monthly limit amounts.
audit.log
A plain-text log of every mutating action. Each line contains a timestamp and the qualified name of the function that was called (e.g. Tracker.add_expense). Written by the @log_action decorator. Safe to delete — the app recreates it automatically.

EXPORTS
Auto-created when the user runs an export. Safe to clear at any time — contains only generated reports, not the source data.
transactions_YYYYMMDD_HHMMSS.json
overall_status_YYYYMMDD_HHMMSS.json

REPORTS
Handles all read-only analysis and file export. Nothing in this package modifies the Tracker.
analytics.py
Computes summaries from the data held in a Tracker instance. Provides: monthly_summary() — income, expenses, savings, and transaction count per calendar month; category_breakdown() — total spent and percentage share per category; overall_stats() — total transactions, total income, total expenses, net balance, average monthly spend and savings, months tracked, and categories used; top_spending_categories() — the top N categories by absolute spending; overdue_budget_warnings() — a generator that yields only the budget status entries where spending exceeded the limit; transaction_by_month() — an internal generator that groups transactions by YYYY-MM label, used by monthly_summary().
exporter.py
Writes export files to the exports/ directory. Creates the directory if it does not exist. Timestamps every filename. Provides export_transactions_json() and export_full_report_json(), both of which return the path of the file written.

STORAGE
The only package that reads from or writes to the file system.
persistence.py
Provides two functions: save() and load(). save() serializes the full Tracker state — all transactions and all budget limits — to data/transaction.json and data/budgets.json, overwriting the previous files. load() reads both files back and reconstructs Transaction and Budget objects from the stored JSON. If either file is missing or empty, load() skips it silently. Any JSON decode error, missing key, or OS error is caught and re-raised as a StorageError. Swapping JSON storage for a database would only require changes to this file.

UTILS
Shared helpers used across all other packages.
exceptions.py
Defines a custom exception hierarchy. All exceptions inherit from FinanceTrackerError, which itself inherits from the built-in Exception. Specific exceptions: InvalidAmountError, InvalidDateError, BudgetExceededError, InsufficientFundsError, CategoryNotFoundError, DuplicateTransactionError, StorageError. Using a custom base class means the CLI can catch all domain errors with a single except FinanceTrackerError clause, while still being able to handle specific cases individually.
validators.py
Contains all input validation logic. Compiled regex patterns: DATE_PATTERN (YYYY-MM-DD), AMOUNT_PATTERN (optional minus, digits, up to 2 decimal places), MERCHANT_PATTERN (characters to strip from merchant names), WHITESPACE (runs of 2 or more spaces). Lambda predicates for use in analytics: is_expense, is_income, in_category (curried), format_money, to_pct. Validation functions: validate_amount() raises InvalidAmountError for non-numeric or zero input; validate_date() raises InvalidDateError for malformed or impossible dates; validate_category() strips and lowercases the input; normalize_merchant() removes special characters, collapses whitespace, and applies title case.
decorators.py
Provides two decorators. @log_action wraps a function so that after it returns successfully, a timestamped line is appended to data/audit.log using the function's qualified name. It logs only on success — if the function raises, nothing is written. @validate_input wraps add_expense and add_income to validate amount and date_str before the function body runs, regardless of whether they were passed as positional or keyword arguments. 



 {
        "id": "c59390fa",
        "amount": 1000.0,
        "category": "salary",
        "merchant": "Job",
        "date": "2026-06-02",
        "note": "salary avance",
        "type": "income"
    },
    {
        "id": "399f3c1e",
        "amount": 200.0,
        "category": "coffee",
        "merchant": "Costa",
        "date": "2026-06-02",
        "note": "dummy spending",
        "type": "expense"
    },
    {
        "id": "7ee036e2",
        "amount": 1000.0,
        "category": "salary",
        "merchant": "Job",
        "date": "2026-05-03",
        "note": "",
        "type": "income"
    },
    {
        "id": "0b7bc949",
        "amount": 300.0,
        "category": "food",
        "merchant": "Lidl",
        "date": "2026-06-03",
        "note": "",
        "type": "expense"
    },
    {
        "id": "44a58718",
        "amount": 20.0,
        "category": "coffee",
        "merchant": "Costa",
        "date": "2026-06-03",
        "note": "",
        "type": "expense"
    },
    {
        "id": "7996b867",
        "amount": 30.0,
        "category": "transport",
        "merchant": "Pkp",
        "date": "2026-06-03",
        "note": "train",
        "type": "expense"
    },
    {
        "id": "010b811b",
        "amount": 1000.0,
        "category": "salary",
        "merchant": "Job",
        "date": "2026-06-03",
        "note": "",
        "type": "income"
    },
    {
        "id": "314b15a9",
        "amount": 200.0,
        "category": "tech",
        "merchant": "Apple",
        "date": "2026-06-03",
        "note": "charger",
        "type": "expense"
    },
    {
        "id": "96a20903",
        "amount": 1000.0,
        "category": "salary",
        "merchant": "Job",
        "date": "2026-06-04",
        "note": "",
        "type": "income"
    },
    {
        "id": "34e5a74d",
        "amount": 2000.0,
        "category": "salary",
        "merchant": "Job",
        "date": "2026-06-03",
        "note": "avance",
        "type": "income"
    }
