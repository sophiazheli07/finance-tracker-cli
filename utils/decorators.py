#log_action is the decorator which writes a timestamp 
# line to data/sudit.log every time a decorated function is called. 
# It uses the datetime module to get the current timestamp 
# and appends it to the log file along with the name of the 
# function being called.

# A decorator is a function that takes another function and returns a modified
# version of it.

from datetime import datetime
from functools import wraps # wraps preserves the metadata of the the original function
from pathlib import Path # path objects are better than just writing pass as a string, 
# path handles OS differences, can be concatenated with "/" and has methods such as: exists(), mkdir(), stat()


from utils.exceptions import InvalidAmountError, InvalidDateError

# the outer function 'log_action' takes a function as argument.
# the inner function 'wrapper' replaces it.
def log_action(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs) # call func first before logging so if it raises exception we won't log success
        log_path = Path("data/audit.log")
        log_path.parent.mkdir(parents=True, exist_ok=True) # create dir if needed # do not raise error if it exists
        with open(log_path, "a", encoding="utf-8") as f: # "a" - mode = append add to the end of the file; explicitly specify UTF-8 encoding for the log file because different systems have different encodings 
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                    f"{func.__qualname__} called\n") # qualifies name: includes class name for method (Tracker.add_expense NOT add_expense)
        return result
    return wrapper


# decorator validates amount and date_str before the function runs.
#  This decorator validates amount and date_str before the function runs.
  
#   The argument extraction is complex because the decorated methods can be called
#   with either positional or keyword arguments:
#   - tracker.add_expense(100, "food", "shop", "2024-01-01") → args
#   - tracker.add_expense(amount=100, ...) → kwargs
  
#   kwargs.get("amount", args[1] if len(args) > 1 else None):
#   First try to get 'amount' from keyword args. If not there, try positional
#   args[1] (index 1 because args[0] is 'self'). If neither exists, None.
  
#   why double-validate here and in the CLI?
#   Defense in depth: the CLI validates for user feedback (nice error messages).
#   This decorator validates at the API level (in case Tracker is used
#   programmatically without the CLI).
def validate_input(func):
    @wraps(func)
    def wrapper(*args, **kwargs):                         
        amount = kwargs.get("amount", args[1] if len(args) > 1 else None)
        date = kwargs.get("date_str", args[4] if len(args) > 4 else None)

        if amount is not None:                           
            try:                                          
                amount = float(amount)
            except ValueError:
                raise InvalidAmountError(amount)

            if amount == 0:
                raise InvalidAmountError(amount)

        if date is not None:
            try:
                datetime.strptime(str(date), "%Y-%m-%d")
            except ValueError:
                raise InvalidDateError(date)

        return func(*args, **kwargs)

    return wrapper                                       

