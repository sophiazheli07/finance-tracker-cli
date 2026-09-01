# main logic class

from datetime import datetime
 
from core.budget import Budget # composite class (tracker) --HAS-A--> component class (budget) (order of creation: component class obj is created then the composite class obj is created then composite clss methods are executed and lastly the component class methods are executed )
from core.transaction import Transaction # Tracker stores a list of Transactions
from utils.decorators import log_action, validate_input # Imports two decorators that will be applied to Tracker methods
from utils.exceptions import (
    CategoryNotFoundError,
    DuplicateTransactionError,
    InsufficientFundsError,
)
from utils.validators import validate_category # validate_category function

class Tracker: # central class of the application, it doesn't inherit from anything special (implicitly inherits from object, as all Python classes do).
    """manage all transactions and limits"""

    def __init__(self): # Constructor — called when you do Tracker(), no arguments besides self — the tracker always starts empty
        self.transactions: list[Transaction] = [] # type hint says this is a list of Transaction objects. Initially empty. We will append Transaction instances to this list as they are created.
        self.budget: Budget = Budget() # Creates a new Budget instance and attaches it to the tracker, this is composition — Tracker uses Budget as a component.
        self.categories: set[str] = set() # set collection — fast membership tests, prevents duplicates. This will store all unique categories used in transactions for easy access and validation.

#   two decorators stacked on top of add_expense.
#   Decorator order matters — they are applied bottom-up, called top-down.
#   So when add_expense is called:
#   1. log_action's wrapper runs first 
#   2. inside that, validate_input's wrapper runs
#   3. inside that, the actual add_expense function runs
#   4. res bubbles back up through validate_input, then log_action
    @log_action
    @validate_input
    def add_expense(
        self, 
        amount: float,
        category: str,
        merchant: str,
        date_str: str, # we pass raw data from the CLI
        note: str = "",
        type: str = "expense",
    ) -> Transaction: # Type annotations on all parameters and return type.  -> Transaction means this function returns a Transaction object
        """add a new expense, check budget and available funds"""
        date = datetime.strptime(date_str, "%Y-%m-%d") # Converts the string date from the CLI into a datetime object
        txn = Transaction( #  Creates the Transaction object.
            amount = abs(float(amount)),
            category = validate_category(category),
            merchant = merchant,
            date = date,
            note = note,
            type = type,
        )
        existing_ids = {t.id for t in self.transactions} #  Set comprehension — builds a set of all existing IDs in one line
        if txn.id in existing_ids:
            raise DuplicateTransactionError(txn.id) # UUID generation is random — collision is extremely unlikely but theoretically possible
        
        month_spent = self._monthly_spending(txn.category, txn.date) # Calls a private helper method (prefix _ means "internal use") Gets total spending in this category for the same month
        self.budget.check(txn.category, month_spent + txn.amount) #  Asks the budget object to check if adding this expense would exceed the limit.

        if self.net_balance() - txn.amount < 0: #  Checks if the user has enough balance for this expense
            raise InsufficientFundsError(txn.category, self.net_balance(), txn.amount)

        self.transactions.append(txn) #  Only reached if all checks passed. Adds the transaction to the list and records the category.
        self.categories.add(txn.category)
        return txn # returns the created transaction so the caller (menu) can display it
    
    @log_action
    @validate_input
    def add_income( # similar to add_expense but no budget or balance checks needed
        self, 
        amount: float,
        category: str,
        merchant: str,
        date_str: str,
        note: str = "",
        type: str = "income",
    ) -> Transaction:
        """add a new income transaction"""
        date = datetime.strptime(date_str, "%Y-%m-%d")
        txn = Transaction(
            amount = abs(float(amount)),  
            category = validate_category(category),
            merchant = merchant,
            date = date,
            note = note,   
            type = type,
        )
        existing_ids = {t.id for t in self.transactions}
        if txn.id in existing_ids:
            raise DuplicateTransactionError(txn.id)

        self.transactions.append(txn)
        self.categories.add(txn.category)
        return txn
    
    @log_action
    def delete_transaction(self, txn_id: str) -> Transaction:
        """delete a transaction by id"""
        for i, txn in enumerate(self.transactions):
            if txn.id == txn_id:
                removed = self.transactions.pop(i)
                return removed
        raise KeyError(f"No transaction found with id: {txn_id}") 
    # enumerate() returns (index, value) pairs — we need the index to use pop().
    # list.pop(i) removes the element at index i and returns it.
    # if no matching ID is found, raises KeyError
    
    @log_action
    def set_budget(self, category: str, amount: float) -> None: # Thin wrapper — delegates to budget.set_limit. i use this so external code only talks to Tracker, not directly to its internal budget object. encapsulation principle
        """set or update budget limit for a category"""
        self.budget.set_limit(category, amount)
        
    # queries

    def get_expenses(self) -> list[Transaction]:
        return [t for t in self.transactions if t.type == "expense"] #   List comprehension — creates a new list containing only expense transactions.

    def get_income(self) -> list[Transaction]:
        return [t for t in self.transactions if t.type == "income"] #   List comprehension — creates a new list containing only income transactions.
    
    def get_by_category(self, category: str) -> list[Transaction]: #   List comprehension — creates a new list containing only transactions in the specified category.
        """return all transactions in a category (case-insensitive)."""
        cat = validate_category(category)
        if cat not in self.categories:
            raise CategoryNotFoundError(category)
        return [t for t in self.transactions if t.category == cat]
    
    def search(self, keyword: str) -> list[Transaction]: # case-insensitive search. Both kw and the target are lowercased before comparison.
        """return all transactions where the merchant or note contains the keyword."""
        kw = keyword.strip().lower()
        return [
            t for t in self.transactions
            if kw in t.merchant.lower() or kw in t.note.lower()
        ]
    
    def totals_by_category(self) -> dict[str, float]: #   Dictionary comprehension. For each category, sums the amounts of all expense transactions in that category. Generator expression inside sum() — lazy evaluation, memory efficient.
        """Return total amount per category"""
        return {
            cat: sum((t.amount for t in self.transactions if t.category == cat and t.type == "expense"))
            for cat in self.categories
        }
    
    def net_balance(self) -> float: # compute total balance. Both income and expenses are stored as positive numbers, so we subtract expenses from income.
        income = sum(t.amount for t in self.transactions if t.type == "income")
        expenses = sum(t.amount for t in self.transactions if t.type == "expense")
        return income - expenses

    
    def budget_status(self) -> list[dict]: # Returns a list of dicts, one per category that has a budget limit. 
        """budget status for every category that has a limit set"""
        totals = self.totals_by_category() 
        return [
            {
                "category": cat,
                "spent": abs(totals.get(cat, 0.0)), # totals.get(cat, 0.0) — returns 0.0 if no spending yet in this category.
                "limit": limit,
                "remaining": max(0.0, limit - totals.get(cat, 0.0)), #  remaining can't go below 0 (don't show negative remaining)
                "over": abs(totals.get(cat, 0.0)) > limit, # bool — True if spent more than limit
            }
            for cat, limit in self.budget.limits.items()           # list comprehension
        ]

    def _monthly_spending(self, category: str, reference: datetime) -> float: #  Private method (underscore prefix)
        """total spent in category for the same year-month"""
        return sum(
            abs(t.amount)
            for t in self.transactions
            if t.type == "expense"
            if t.category == category
            and t.date.year == reference.year
            and t.date.month == reference.month
        ) #  returns total spending in a specific category for a specific month. Used by add_expense to check against budget limits

    def _monthly_income(self, reference: datetime) -> float:
        return sum(
            t.amount
            for t in self.transactions
            if t.type == "income"
            and t.date.year == reference.year
            and t.date.month == reference.month
        ) # similar to _monthly_spending but for income. Used in monthly summary report.
