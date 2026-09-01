from utils.exceptions import BudgetExceededError

class Budget:
    """Holds monthly spending limits and checks them against actual spendings."""
    def __init__(self, limits: dict[str, float] | None = None): # just None is a type hint if it is None = None (if no args passed = yse None as default value)#  means this parameter can be either dict[str, float] OR None i use this instead of (self, limits ={}) because mutable defaults are shared between all instances. in my implementation i create a new dict each time (i don't want unexpected behaviour or data collisions)
        self.limits: dict[str, float] = limits or {} # label the type of self.limits for better readability and type checking. if limits is None, use an empty dict instead.

    #manage limits

    def set_limit(self, category: str, amount: float) -> None: 
        """set or update the budget limit for a category."""
        
        if amount <= 0:
            raise ValueError("Budget limit must be a positive number.")
        
        self.limits[category.lower()] = amount #  Always stores categories in lowercase for consistent lookup

    def remove_limit(self, category: str) -> None:
        """remove the limit for a category (is it was set)."""
        self.limits.pop(category.lower(), None) # removes key and returns its value, or returns default if key doesn't exist. None as default means no exception if key is missing.

    def check(self, category: str, curr_spending: float) -> None:
        """Raise BudgetExceededError if current_spending exceeds the limit."""
        category = category.lower()
        if category in self.limits and curr_spending > self.limits[category]:
            raise BudgetExceededError(category, curr_spending, self.limits[category])
    # only raises if BOTH conditions are true:
    #   1. A limit exists for this category
    #   2. Current spending exceeds that limit
    # if no limit is set, no check is performed.
        
    def status(self, category: str, spent: float) -> str:
        """Return (spent, limit, remaining) for a category. Returns (spent, 0, 0) if no limit is set for the category."""
        cat = category.lower()
        limit = self.limits.get(cat, 0.0)
        remaining = max(0.0, limit - spent) if limit > 0 else 0.0
        return (spent, limit, remaining)
    
    # serialization for storage
    def to_dict(self) -> dict: 
        """Convert the budget limits to a dict for JSON storage."""
        return dict(self.limits) # creates a shallow copy of the limits dict; i use copy so caller can't accidentally modify the internal limits by modifying the returned dict. Defensive copy.
    #  difference between @classmethod and @staticmethod:
    #   @staticmethod: no access to class or instance, just a plain function grouped in the class namespace
    #   @classmethod: receives the class itself as first argument (cls)
    
    @classmethod # this method creates a new instance — it doesn't have an instance to receive. it's called as: Budget.from_dict(some_dict)
    def from_dict(cls, data: dict) -> "Budget": # forward reference to the class itself in the return type annotation (since Budget is not fully defined yet at this point in the code)
        return cls(limits = {k: float(v) for k, v in data.items()}) # dict comprehension that converts all values to float
    
    def __repr__(self) -> str: # represent the Budget object as a string for debugging purposes. this is what we see when print a list of transactions that include a Budget object, or when inspect the object in a debugger. without __repr__ it could look like this : <core.budget.Budget object at 0x7f8c9d2e5b50>" which is not informative
        return f"Budget(limits={self.limits})" 