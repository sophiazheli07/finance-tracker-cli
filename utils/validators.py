# File validators.py contain: all regex patterns, all lambda 
# definitions, and standalone validation functions. 
# This is where regex criterion and lambda criterion located

from utils.exceptions import InvalidAmountError, InvalidDateError
import re # 're' is the standard library regular expression module.
from datetime import datetime

# compiled regex patterns
# i use compiled patterns because they are more efficient for repeated use
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$") # re.compile() compiles a regex pattern into a reusable Pattern object
MERCHANT_PATTERN = re.compile(r"[^\w\s\-&]") 
WHITESPACE = re.compile(r"\s{2,}")
AMOUNT_PATTERN = re.compile(r"^-?\d+(\.\d{1,2})?$")


# one liner predicates that can be reused
# Lambda functions — anonymous one-line functions.
is_expense = lambda t: t.type == "expense"
is_income  = lambda t: t.type == "income"
in_category  = lambda cat: (lambda t: t.category == cat)  #curried function — a function that returns another function  in_category("groceries") returns a lambda that checks if t.category == "groceries" This allows: filter(in_category("groceries"), transactions)
format_money = lambda amt: f"{amt:,.2f}" #  formats a number with commas and 2 decimal places.
to_pct       = lambda part, total: round(part / total * 100, 1) if total else 0.0

# validation functions that take user input, validate with regex 
# convert to correct type, and return the value or raise an exception if invalid. 
# the cli calls these before passing values to tracker

def validate_amount(raw_string: str) -> float: # validates the look of the input and checks if it's a valid amount 
    raw = raw_string.strip()
    if not AMOUNT_PATTERN.match(raw):
        raise InvalidAmountError(raw_string)
    
    value = float(raw)
    if value == 0:
        raise InvalidAmountError(raw_string)
    return value
    

def validate_date(raw_string: str) -> datetime: # validates the look of the input anf checks if the date is valid: for examle we can have 
    # 2026.05.41 - it is valid wih regex but it is not a real date - so it will fail with datetime check 
    raw = raw_string.strip()
    if not DATE_PATTERN.match(raw):
        raise InvalidDateError(raw_string)
    try:
        return datetime.strptime(raw, "%Y-%m-%d")
    except ValueError:
        raise InvalidDateError(raw_string)
    
def normalize_merchant(raw_string: str) -> str:  
    # MERCHANT_PATTERN.sub("", raw) — replaces all matches of MERCHANT_PATTERN with ""
    #   (removes them).
    #   WHITESPACE.sub(" ", cleaned) — replaces runs of whitespace with single space.
    #   .title() — capitalizes the first letter of each word: "zabka store" → "Zabka Store"

    raw = raw_string.strip()
    cleaned = MERCHANT_PATTERN.sub("", raw) # substitute all special characters with empty string (remove them)
    normalized = WHITESPACE.sub(" ", cleaned) # replace runs of whitespace with single space
    return normalized.title() # capitalize the first letter of each word

def validate_category(raw_string: str) -> str: # normalizes the category by stripping whitespace, collapsing multiple spaces, and converting to lowercase. 
    stripped = WHITESPACE.sub(" ", raw_string.strip())
    return stripped.lower()


# regex exp 
#   DATE_PATTERN
# ^ - start string, $ - end string
#  \d{4} - exactly 4 digits (year)
#  - - literal dash
#  \d{2} - exactly 2 digits (month)
#  - - literal dash
#  \d{2} - exactly 2 digits (day)
# matches: "2024-01-15" — does NOT match "2024-1-5" or "not-a-date"

# MERCHANT_PATTERN
# [^...]  = character class negation — matches any char NOT in the class
#  \w      = word character (letters, digits, underscore)
#  \s      = whitespace
#  \-      = literal hyphen (escaped inside [...] to avoid range interpretation)
#   &       = literal ampersand
#    Matches any character that is NOT a word char, space, hyphen, or ampersand.
#    Removes special characters from merchant names.

#  WHITESPACE
#  \s{2,} = 2 or more consecutive whitespace characters
#  Used to collapse "multiple   spaces" into "multiple spaces"

#  AMOUNT_PATTERN:
#     -?  = optional minus sign
#     \d+ = one or more digits
#     (\.\d{1,2})? = optional group: decimal point followed by 1 or 2 digits
#     Matches: "49.99", "1000", "-50", "0.5"
#     Does NOT match: "abc", "1.999" (3 decimal places), ""
