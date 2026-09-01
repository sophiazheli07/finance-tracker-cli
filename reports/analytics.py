from collections import defaultdict # subclass of dict. automatically initializes value for a key that does not exist yet to prevent KeyError

from core.tracker import Tracker
from utils.validators import is_expense, is_income, to_pct

#this is a generator function (instead of building a full dict in memory and returning it, it yields one item at a time (memory efficient)
def transaction_by_month(tracker: Tracker):
    """yield (month_label, [transactions]) in chronological order."""
    grouped: dict[str, list] = defaultdict(list) # label = grouped #  creates a dict where any missing key automatically gets an empty list as its default value.
    # if i haven't used defaultdict, i would have to check if the month key exists in the dict before appending to the list and manually create list first
    for t in tracker.transactions:
        grouped[t.date.strftime("%Y-%m")].append(t) 
    for month in sorted(grouped): #  sorts month strings alphabetically, which happens to be chronologically correct because of the YYYY-MM format.
        yield month, grouped[month] #  yields a tuple of (month_string, list_of_transactions)

#another generator function that yields only the status dicts where spending exceeded limit.
def overdue_budget_warnings(tracker: Tracker):
    """yield status dicts for categories that have exceeded budget"""
    for status in tracker.budget_status():
        if status["over"]:
            yield status

# monthly summary 

def monthly_summary(tracker: Tracker) -> dict[str, dict]:
    """per-month income, expenses, and net for the whole history"""
    return {
        month: {
            "income":   sum(t.amount for t in txns if is_income(t)),
            "expenses": sum(abs(t.amount) for t in txns if is_expense(t)),
            "net":      sum(t.amount for t in txns if is_income(t)) - sum(abs(t.amount) for t in txns if is_expense(t)),
            "savings":  sum(t.amount for t in txns if is_income(t)) - sum(abs(t.amount) for t in txns if is_expense(t)),
            "count":    len(txns),
        }
        for month, txns in transaction_by_month(tracker)
    } # nested dict comprehension; Outer comprehension iterates over months; Inner dict is built for each month.

# categories summary

def top_spending_categories(tracker: Tracker, n: int = 5) -> list[tuple[str, float]]:
    """the top-n categories by absolute spending, descending"""
    totals = tracker.totals_by_category()
    return sorted(totals.items(), key=lambda x: abs(x[1]), reverse=True)[:n]

def category_breakdown(tracker: Tracker) -> list[dict]:
    """full breakdown: category, total spent, % of all spending."""
    totals = tracker.totals_by_category()
    total_spent = sum(totals.values())
    return sorted(
        [
            {
                "category": cat,
                "spent": abs(amount),
                "pct": to_pct(abs(amount), total_spent)
            }
            for cat, amount in totals.items() if amount > 0
        ],
        key = lambda x: x["spent"],
        reverse = True
    ) # builds a list of dicts, one per category, sorted by amount spent. to_pct calculates what percentage of total spending this category represents

def overall_stats(tracker: Tracker) -> dict:
    """all the staistics in one place: total income, total expenses, net balance, and budget status."""
    income_txns = [t for t in tracker.transactions if is_income(t)]
    expense_txns = [t for t in tracker.transactions if is_expense(t)]

    total_income = sum(t.amount for t in income_txns)
    total_expenses = sum(abs(t.amount) for t in expense_txns)
    total_savings  = total_income - total_expenses

    months = set(t.date.strftime("%Y-%m") for t in tracker.transactions)
    month_count = len(months) or 1

    return {
        "total_transactions": len(tracker.transactions), # len of the list
        "total_income":       total_income,
        "total_expenses":     total_expenses,
        "net_balance":        tracker.net_balance(), # net balance calculated by tracker
        "total_savings":      total_savings,
        "avg_monthly_spend":  round(total_expenses / month_count, 2), # round to 2 decimal places for better readability. cal
        "avg_monthly_savings": round(total_savings  / month_count, 2),
        "months_tracked":     month_count,
        "categories_used":    len(tracker.categories)
    }
