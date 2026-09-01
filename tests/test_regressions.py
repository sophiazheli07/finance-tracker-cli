from pathlib import Path

import pytest

from core.tracker import Tracker
from core.transaction import Transaction
from storage import persistence
from utils.exceptions import (
    BudgetExceededError,
    CategoryNotFoundError,
    InsufficientFundsError,
)
# pytest fixtures 
 
# tmp_path gives you a fresh, empty, temporary directory 
# (a pathlib.Path object) unique to each test. It's deleted 
# after the test suite finishes. Perfect for tests that need 
# to read/write files without polluting your real project.

# monkeypatch lets you temporarily change things — environment variables, 
# object attributes, the current working directory, etc. — for the 
# duration of one test. Changes are automatically undone after the test ends.
def test_expense_sign_consistency(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tracker = Tracker()

    tracker.add_income(
        amount=1000,
        category="salary",
        merchant="Job",
        date_str="2026-05-01",
    )
    txn = tracker.add_expense(
        amount=50,
        category="food",
        merchant="Shop",
        date_str="2026-05-02",
    )

    assert txn.amount == 50.0
    assert txn.type == "expense"


def test_budget_exceed_check(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tracker = Tracker()

    tracker.add_income(
        amount=1000,
        category="salary",
        merchant="Job",
        date_str="2026-05-01",
    )
    tracker.set_budget("food", 100)
    tracker.add_expense(
        amount=70,
        category="food",
        merchant="Shop",
        date_str="2026-05-02",
    )

    with pytest.raises(BudgetExceededError):
        tracker.add_expense(
            amount=40,
            category="food",
            merchant="Shop",
            date_str="2026-05-03",
        )


def test_insufficient_funds_check(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tracker = Tracker()

    with pytest.raises(InsufficientFundsError):
        tracker.add_expense(
            amount=10,
            category="food",
            merchant="Shop",
            date_str="2026-05-01",
        )


def test_category_exception_type():
    tracker = Tracker()

    with pytest.raises(CategoryNotFoundError):
        tracker.get_by_category("does-not-exist")


def test_first_run_save_creates_data_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tracker = Tracker()

    persistence.save(tracker)

    assert Path("data").exists()
    assert Path("data/transaction.json").exists()
    assert Path("data/budgets.json").exists()


def test_legacy_negative_expense_normalization():
    tx = Transaction.from_dict(
        {
            "id": "abc12345",
            "amount": -25,
            "category": "food",
            "merchant": "shop",
            "date": "2026-05-01",
            "type": "expense",
            "note": "legacy",
        }
    )

    assert tx.amount == 25.0