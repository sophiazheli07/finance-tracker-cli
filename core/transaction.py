#The uuid module generates universally unique identifiers (UUIDs) according to RFC 4122(the primary internet standard defining Universally Unique Identifiers (UUIDs)).

# dataclasses module helps write classes that mainly store data
# by generating methods like __init__, __repr__, and comparisons.

# Use it to reduce boilerplate for simple data containers, 
# customize fields with defaults/metadata, and convert instances
# to dicts/tuples.

# Literal allows us to specify that a variable can only take on specific string values.
# 'typing.Literal' is part of the Python standard library.
from typing import Literal
# 'uuid' - Universally Unique Identifier.
#   it's a standard library module that generates random ids like:
#   "550e8400-e29b-41d4-a716-446655440000"
#   these IDs are statistically guaranteed to be unique — the probability of two
#   being the same is astronomically small (1 in 2^122).
#   i used  UUIDs for transaction IDs instead of 1, 2, 3, because:
#   sequential integers can cause problems if data is merged from multiple sources
#   (two files might both have transaction "5"). UUIDs are always unique regardless
#   of where they were generated.
import uuid
from datetime import datetime  # we need datetime objects to store the date of a transaction
from dataclasses import dataclass, field #  'dataclasses' is a standard library module introduced in Python
#   '@dataclass' is a decorator that automatically generates:
#   - __init__: the constructor method
#   - __repr__: string representation for debugging
#   - __eq__: equality comparison
# without @dataclass, writing a Transaction class would require about 20 lines
#   just for __init__ (one line per field assignment). @dataclass reduces that
#   to zero — the fields ARE the constructor.
# 'field' is used to specify special behavior for individual fields

from utils.validators import normalize_merchant, validate_category

#  This decorator transforms the Transaction class below into a dataclass.
#   It reads the class-level type-annotated variables and generates __init__
#   automatically. So 'amount: float' becomes a parameter in __init__.
# This module provides a decorator and functions for automatically adding generated 
# special methods such as __init__() and __repr__() to user-defined classes. 
@dataclass 
class Transaction: # this class represents ONE financial transaction with minimal logic 
    """represents a single financial transaction with attributes like amount, date, category, and merchant.""" # docstring describing the class

    amount: float
    category: str
    merchant: str
    date: datetime # we use datetime objects to store the date of a transaction, which allows for easy formatting and comparison. The __post_init__ method will handle converting from string to datetime if needed.
    # somewhat enums 
    type: Literal["income", "expense"] # type annotation says this field must be exactly "income" or "expense". nothing else is valid. this is enforced by type checkers 
    note: str = "" #  optional field with a default value of empty string. In a @dataclass, fields with defaults MUST come after fields without defaults
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8]) # 'field()' allows specifying more complex default behavior. 'default_factory' is called every time a new Transaction is created.

    def __post_init__(self): #   __post_init__ is a special @dataclass method called automatically AFTER  __init__ runs (use it to normalize data (clean up merchant (remove unnecesary whitespace, standardize capitalization) and validate category (check if it's in the predefined set)).
        # i use clean up data in this method in this method instead of __init__ because Transaction objects can also be created from JSON data and i want normalization to happen regardles where the Transaction is created from.
        self.merchant = normalize_merchant(self.merchant)
        self.category = validate_category(self.category)
        # Keep amount sign consistent across app logic.
        if self.type == "expense":
            self.amount = abs(float(self.amount))
        elif self.type == "income":
            self.amount = abs(float(self.amount))

    @classmethod # recieves the class itself as the first arg instead of instance (self)
    # this method creates a new instance — it doesn't have an instance to receive. it's called as: Transaction.from_dict(some_dict)
    def from_dict(cls, data: dict):
        """Creates a Transaction instance from a dictionary."""
        #  This is the Factory Method design pattern: a class method that constructs instances from different data formats.
        return cls(
            amount=float(data["amount"]), # dict lookup, raises KeyError if "amount" key is missing
            category=data["category"], # converts string "50" to float 50.0
            merchant=data["merchant"],
            date=datetime.strptime(data["date"], "%Y-%m-%d"), # __post_init__ will handle the string-to-date conversion
            type=data.get("type", "expense" if float(data["amount"]) < 0 else "income"),
            note=data.get("note", ""),
            id=data.get("id")  # keep the original ID if it exists
    )
    
    def to_dict(self): # converts the Transaction to a plain Python dictionary for JSON serialization.
        """Convert to a JSON-serializable dict for storage or display."""
        return {
            "id": self.id,
            "amount": self.amount,
            "category": self.category,
            "merchant": self.merchant,
            "date": self.date.strftime("%Y-%m-%d"),
            "note": self.note,
            "type": self.type
        }
    
    # The __str__ method provides a human-readable string representation of the transaction,
    # 9 - minimum total width of the amount field, .2f - format as a float with 2 decimal places, and abs() to show the amount absolute value (without sign).
    def __str__(self):
        tag = "INC" if self.type == "income" else "EXP"
        return (
            f"[{self.id}] {self.date.strftime("%Y-%m-%d")} "
            f"{tag}{abs(self.amount):>12.2f} "
            f"{self.category:<15}  {self.merchant:<10}"
        )

#   :>9.2f — right-align (>) in a field 9 characters wide, 2 decimal places, float
#   :<15   — left-align (<) in a field 15 characters wide
#   :<20   — left-align in a field 20 characters wide