#menu, inputs, display formatting

from datetime import datetime
 
from core.tracker import Tracker
from reports.analytics import (
    category_breakdown,
    monthly_summary,
    overall_stats,
    overdue_budget_warnings,
    top_spending_categories,
)
from reports.exporter import (
    export_full_report_json,
    export_transactions_json,
)
from storage import persistence
from utils.exceptions import (
    BudgetExceededError,
    CategoryNotFoundError,
    FinanceTrackerError,
    InsufficientFundsError,
    InvalidAmountError,
    InvalidDateError,
)
from utils.validators import validate_amount, validate_category, validate_date

LINE = "─" * 60
THIN = "·" * 60
width = 60

def header(title: str) -> None:
    print(f"\n{LINE}")
    print(f"  {title}")
    print(LINE)

def success(msg: str) -> None:
    print(f" SUCCESS: {msg}")

def error(msg: str) -> None:
    print(f" ERROR: {msg}")

def info(msg: str) -> None:
    print(f" INFO: {msg}")

def prompt(label: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    raw = input(f"  {label}{hint}: ").strip()
    return raw if raw else default

# main menu
def main_menu() -> None:
    print(f"\n{'═' * 60}")
    print("Personal Finance Tracker".center(width))
    print(f"{'═' * 60}")
    options = [
        ("0", "Add income"), 
        ("1", "Add expense"),      
        ("2", "List transactions"),
        ("3", "Search transactions"),
        ("4", "Delete transaction"),
        ("5", "Category summary"),
        ("6", "Monthly summary"),
        ("7", "Overall statistics"),
        ("8", "Budget limits"),
        ("9", "Export data"),
        ("x", "Exit"),
    ]
    for key, label in options:
        print(f"  [{key}]  {label}")
    print(LINE)

# add trans

def add_expense_menu(tracker: Tracker) -> None:
    header("Add Expense".center(width))

    while True:
        try:
            amount = validate_amount(prompt("Amount (e.g. 49.99)"))
            break
        except InvalidAmountError as e:
            error(str(e))

    category = validate_category(prompt("Category (e.g. groceries)"))
    merchant = prompt("Merchant (e.g. Zabka)") or "Unknown"

    while True:
        raw_date = prompt("Date (YYYY-MM-DD)", default=datetime.now().strftime("%Y-%m-%d"))
        try:
            validate_date(raw_date)
            break
        except InvalidDateError as e:
            error(str(e))

    note = prompt("Note (optional)")

    try:
        txn = tracker.add_expense(
            amount=amount, category=category,
            merchant=merchant, date_str=raw_date, note=note, type="expense",
        )
        persistence.save(tracker)
        success(f"Expense added: {txn}")

        for w in overdue_budget_warnings(tracker):
            over_by = w["spent"] - w["limit"]
            print(f"\n  !!! Budget warning: '{w['category']}' over by {over_by:.2f} !!!")

    except InsufficientFundsError as e:        #  specific first
        error(str(e))
        answer = prompt("This will put you in negative balance. Proceed? (yes/no)", default="no")
        if answer.lower() in ("yes", "y"):
            from core.transaction import Transaction
            date = datetime.strptime(raw_date, "%Y-%m-%d")
            txn = Transaction(
                amount=abs(amount), category=category,
                merchant=merchant, date=date, type="expense", note=note,
            )
            tracker.transactions.append(txn)
            tracker.categories.add(txn.category)
            persistence.save(tracker)
            success(f"Expense added (negative balance): {txn}")
        else:
            info("Transaction cancelled.")

    except BudgetExceededError as e:           #  specific second
        error(str(e))
        answer = prompt("Add anyway? (yes/no)", default="no")
        if answer.lower() in ("yes", "y"):
            from core.transaction import Transaction
            date = datetime.strptime(raw_date, "%Y-%m-%d")
            txn = Transaction(
                amount=abs(amount), category=category,
                merchant=merchant, date=date, type="expense", note=note,
            )
            tracker.transactions.append(txn)
            tracker.categories.add(txn.category)
            persistence.save(tracker)
            success(f"Expense added (over budget): {txn}")
        else:
            info("Transaction cancelled.")

    except FinanceTrackerError as e:           #  base class last
        error(str(e))
    


def add_income_menu(tracker: Tracker) -> None:
    header("Add Income".center(width))

    while True:
        try:
            amount = validate_amount(prompt("Amount (e.g. 5000.00)"))
            break
        except InvalidAmountError as e:
            error(str(e))

    category = validate_category(prompt("Category (e.g. salary)"))
    merchant = prompt("Source (e.g. Employer)") or "Unknown"

    while True:
        raw_date = prompt("Date (YYYY-MM-DD)", default=datetime.now().strftime("%Y-%m-%d"))
        try:
            validate_date(raw_date)
            break
        except InvalidDateError as e:
            error(str(e))

    note = prompt("Note (optional)")

    try:
        txn = tracker.add_income(
            amount=amount, category=category,
            merchant=merchant, date_str=raw_date, note=note, type="income",
        )
        persistence.save(tracker)
        success(f"Income added: {txn}")
    except FinanceTrackerError as e:
        error(str(e))

    
# list trans

def prompt_list_transactions(tracker: Tracker) -> None:
    header("Transactions".center(width))

    if not tracker.transactions:
        info("No transaction recorded yet.")
        return
    
    print("Filter by:  [1] All  [2] Expenses  [3] Income only  [4] Category")
    choice = prompt("Filter", "1")

    if choice == "2":
        txns = tracker.get_expenses()
        label = "Expenses"
    elif choice == "3":
        txns = tracker.get_income()
        label = "Income"
    elif choice == "4":
        if not tracker.categories:
            info("No categories yet.")
            return
        print("\n  Available categories: " + ", ".join(sorted(tracker.categories)))
        cat = validate_category(prompt("Enter category"))
        try:
            txns = tracker.get_by_category(cat)
            label = f"Category: {cat}"
        except CategoryNotFoundError as e:
            error(str(e))
            return
    else:
        txns = tracker.transactions
        label = "All transactions"


    print(f"\n  {label} ({len(txns)} records)")
    print(f"{THIN}")
    print(f"{'ID':<8}  {'Date':<12}  {'Amount':>10}  {'Category':<15}  Merchant")
    print(f"{THIN}")
    for t in sorted(txns, key=lambda x: x.date, reverse=True):
        print(f"  {t}")
    print(f"{THIN}")
    if choice == "2":
        total = -sum(t.amount for t in txns)
        total_label = "Total expenses"
    elif choice == "3":
        total = sum(t.amount for t in txns)
        total_label = "Total income"
    else:
        # Amounts are stored as positive values, so compute signed net.
        total = sum(t.amount if t.type == "income" else -t.amount for t in txns)
        total_label = "Net total"
    print(f"  {total_label:>37}  {total:>+10.2f}")

# search

def prompt_search(tracker: Tracker) -> None:
    header("Search transactions".center(width))
    keyword = prompt("Search keyword (in merchant or note)")
    if not keyword:
        info("No keyword entered.")
        return
    
    results = tracker.search(keyword)
    if not results:
        info(f"No transactions matching '{keyword}'.")
        return
    
    print(f"\n  Found {len(results)} result(s) for '{keyword}':")
    print(f"{THIN}")
    for t in results:
        print(f"  {t}")
        if t.note:
            print(f"     Note: {t.note}")

# delete

def prompt_delete_transaction(tracker: Tracker) -> None:
    header("Delete transaction".center(width))
    if not tracker.transactions:
        info("No transactions to delete.")
        return
 
    txn_id = prompt("Transaction ID to delete")
    if not txn_id:
        return
 
    try:
        txn = tracker.delete_transaction(txn_id)
        persistence.save(tracker)
        success(f"Deleted: {txn}")
    except KeyError as e:
        error(str(e))

# category summary

def prompt_category_summary(tracker: Tracker) -> None:
    header("Category summary".center(width))
 
    breakdown = category_breakdown(tracker)
    if not breakdown:
        info("No expense data yet.")
        return
 
    budgets = {row["category"]: row for row in tracker.budget_status()}
 
    print(f"\n  {'Category':<15}  {'Spent':>10}  {'% Total':>8}  {'Budget':>9}  {'% Budget':>9}  {'Status'}")
    print(f"{THIN}")
    for row in breakdown:
        cat = row["category"]
        budget_row = budgets.get(cat)
        if budget_row:
            budget_str = f"{budget_row['limit']:>9.2f}"
            usage_pct = (row["spent"] / budget_row["limit"] * 100) if budget_row["limit"] else 0.0
            budget_pct_str = f"{usage_pct:>8.1f}%"
            status = "OVER" if budget_row["over"] else f"  {budget_row['remaining']:.2f} left"
        else:
            budget_str = f"{'—':>9}"
            budget_pct_str = f"{'—':>9}"
            status = ""
        print(f"  {cat:<15}  {row['spent']:>10.2f}  {row['pct']:>7.1f}%  {budget_str}  {budget_pct_str}  {status}")

# monthly summary
def prompt_monthly_summary(tracker: Tracker) -> None:
    header("Monthly summary".center(width))
 
    summary = monthly_summary(tracker)
    if not summary:
        info("No transaction data yet.")
        return
 
    print(f"\n  {'Month':^10}  {'Income':^10}  {'Expenses':^10}  {'Savings':^10}  {'txns':^6}")
    print(f"{THIN}")
    for month, data in sorted(summary.items(), reverse=True):
        savings = data["savings"]
        savings_str = f"{savings:^+10.2f}"
        print(
            f"  {month:^10}  {data['income']:^10.2f}  {data['expenses']:^10.2f}"
            f"  {savings_str}  {data['count']:^6}"
        )
        
# overall stats

def prompt_overall_stats(tracker: Tracker) -> None:
    header("Overall statistics".center(width))
 
    stats = overall_stats(tracker)
    pairs = [
        ("Total transactions",   stats["total_transactions"]),
        ("Months tracked",       stats["months_tracked"]),
        ("Categories used",      stats["categories_used"]),
        ("Total income",         f"{stats['total_income']:,.2f}"),
        ("Total expenses",       f"{stats['total_expenses']:,.2f}"),
        ("Net balance",          f"{stats['net_balance']:+,.2f}"),
        ("Avg monthly spend",    f"{stats['avg_monthly_spend']:,.2f}"),
        ("Avg monthly savings",   f"{stats['avg_monthly_savings']:+,.2f}"),
    ]
    for label, value in pairs:
        print(f"  {label:<25}  {value}")
 
    print(f"\n  Top spending categories:")
    for cat, spent in top_spending_categories(tracker, n=5):
        print(f"    {cat:<20}  {spent:,.2f}")

# budget limits

def prompt_budget_menu(tracker: Tracker) -> None:
    header("Budget limits".center(width))
    print("  [1] Set / update a limit")
    print("  [2] Remove a limit")
    print("  [3] View all limits")
    choice = prompt("Option", "3")
 
    if choice == "1":
        cat = validate_category(prompt("Category"))
        while True:
            try:
                limit = validate_amount(prompt("Monthly limit (positive)"))
                if limit < 0:
                    raise InvalidAmountError(limit)
                break
            except InvalidAmountError as e:
                error(str(e))
        tracker.set_budget(cat, abs(limit))
        persistence.save(tracker)
        success(f"Budget set: {cat} → {abs(limit):.2f} / month")
 
    elif choice == "2":
        cat = validate_category(prompt("Category to remove"))
        tracker.budget.remove_limit(cat)
        persistence.save(tracker)
        success(f"Budget limit removed for '{cat}'.")
 
    else:
        if not tracker.budget.limits:
            info("No budget limits set yet.")
            return
        print(f"\n  {'Category':<20}  {'Limit':>10}")
        print(f"{THIN}")
        for cat, limit in sorted(tracker.budget.limits.items()):
            print(f"  {cat:<20}  {limit:>10.2f}")

# export

def prompt_export(tracker: Tracker) -> None:
    header("Export data".center(width))
    print("  [1] Transactions -> JSON")
    print("  [2] Full report -> JSON")
    choice = prompt("Option", "1")
 
    export_fn = {
        "1": export_transactions_json,
        "2": export_full_report_json,
    }.get(choice)
 
    if not export_fn:
        error("Invalid option.")
        return
 
    if not tracker.transactions:
        info("No data to export.")
        return
 
    path = export_fn(tracker)
    success(f"Exported to: {path}")