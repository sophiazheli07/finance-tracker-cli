#instead of using ValueError or RuntimeError i decided to create custom exceptions so we would recieve 
# descriptive, specific and specifically caugth exceptions

class FinanceTrackerError(Exception): # base class for any exception we would have during the development
    # Inherits from the built-in Exception class
    """Base exception for all finance tracker errors."""

    def __init__(self, message: str):
        super().__init__(message) #   super().__init__(message) passes the message to Exception's __init__, which stores it


class InvalidAmountError(FinanceTrackerError):
    def __init__(self, value):
        super().__init__(f"Invalid amount: '{value}'")


class InvalidDateError(FinanceTrackerError):
    def __init__(self, value):
        super().__init__(f"Invalid date: '{value}'")


class BudgetExceededError(FinanceTrackerError):
    def __init__(self, category: str, spent: float, limit: float):
        super().__init__(
            f"Budget exceeded for '{category}': spent {spent:.2f} of {limit:.2f}"
        )


class InsufficientFundsError(FinanceTrackerError):
    def __init__(self, category: str, balance: float, expense: float):
        super().__init__(
            f"Insufficient funds for '{category}': balance {balance:.2f}, expense {expense:.2f}"
        )


class CategoryNotFoundError(FinanceTrackerError):
    def __init__(self, category):
        super().__init__(f"Category '{category}' not found.")


class DuplicateTransactionError(FinanceTrackerError):
    def __init__(self, transaction_id):
        super().__init__(f"Duplicate transaction ID: '{transaction_id}'")


class StorageError(FinanceTrackerError):
    def __init__(self, path: str, reason: str):
        super().__init__(f"Storage error at '{path}': {reason}")