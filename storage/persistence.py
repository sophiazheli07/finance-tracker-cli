# save load data to/from a file
# json - javascript object notation - human readable, widely supported, can represent complex nested data structures (lists, dicts), but not custom classes directly (need to convert to dict first)
# json for storage as it is :
# - humanreadable
# - widely supported
# - simple structire that matches Py datatypes dicts
import json
from pathlib import Path

from core.budget import Budget
from core.transaction import Transaction
from core.tracker import Tracker
from utils.exceptions import StorageError

DATA_DIR = Path("data")
TRANSACTIONS_FILE = Path("data/transaction.json") # correct path handling across OS
BUDGETS_FILE = Path("data/budgets.json")

def data_exists() -> bool: # check if both files exist 
    return Path("data").exists() and TRANSACTIONS_FILE.exists() and BUDGETS_FILE.exists()

def save(tracker: Tracker) -> None:
    """save transactions and budgets to json files"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        # i overwrite and not append because we want to save the current state of the tracker, not add to it. if the file doesn't exist, it will be created. if it exists, it will be overwritten with the new data.
        # open( ) is a context manager - it will automtically close the file when doen even if error occures 
        # if i would have use "a" mode it would have created a new file with the new data instead of overwriting the existing file, which would lead to duplicate data and incorrect loading later.
        with open(TRANSACTIONS_FILE, "w", encoding="utf-8") as f: # open file with "w" mode - write (overwrites existing file or create new one if it doesn't exist) and specify UTF-8 encoding for consistency across systems
            json.dump(
                [t.to_dict() for t in tracker.transactions], # List comprehension that converts each Transaction to a dict. JSON can't serialize Transaction objects directly.
                f,
                indent=4,
                ensure_ascii=False,
            )
            # json.dump takes a Python object and writes it as JSON to the file.
            # dump(what, where, pretty print(indent), ensure_ascii=False to allow non-ASCII characters in the output(we want to allow Żabka))


        with open(BUDGETS_FILE, "w", encoding="utf-8") as f: # open file with "w" mode - write (overwrites existing file or create new one if it doesn't exist) and specify UTF-8 encoding for consistency across systems
            json.dump(
                tracker.budget.to_dict(), 
                f, 
                indent=4, 
                ensure_ascii=False
            )
    except OSError as e:
        raise StorageError(str(TRANSACTIONS_FILE), str(e))
    
def load(tracker: Tracker) -> None:
    data_exists()

    if TRANSACTIONS_FILE.exists() and TRANSACTIONS_FILE.stat().st_size > 0: #  def st_size(self) -> int: ...  # size of file, in bytes ensure that the file is not empty othewise load() will fail
        try:
            with open(TRANSACTIONS_FILE, "r", encoding="utf-8") as f: # open file with "r" mode - read and specify UTF-8 encoding 
                raw = json.load(f) # load JSON data from file and parse it into Python objects (in this case, a list of dicts representing transactions). if the file is not valid JSON, this will raise a JSONDecodeError, which we catch and re-raise as StorageError with more context.
            for item in raw: # reconstracts Transaction objects from the list of dicts loaded from JSON. if the JSON structure is incorrect (missing keys, wrong types), this could raise a KeyError or ValueError, which we catch and re-raise as StorageError with more context.
                txn = Transaction.from_dict(item)
                tracker.transactions.append(txn)
                tracker.categories.add(txn.category)
        except (json.JSONDecodeError, KeyError, OSError) as e:
            raise StorageError(str(TRANSACTIONS_FILE), str(e))
        
    if BUDGETS_FILE.exists() and BUDGETS_FILE.stat().st_size > 0:
        try:
            with open(BUDGETS_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            tracker.budget = Budget.from_dict(raw)
        except (json.JSONDecodeError, KeyError, OSError) as e:
            raise StorageError(str(BUDGETS_FILE), str(e))