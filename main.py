"""Personal Finance Tracker — entry point."""
 
import sys # for sys.exit() to exit the program

#  Explicit imports are better practice because:
#   - we can see exactly what this file depends on
#   - it avoids name collisions (two modules might define a function with the same name)
#   - it makes the code easier to understand and maintain
from cli.menu import (
    add_expense_menu,
    add_income_menu,
    main_menu,
    prompt_budget_menu,
    prompt_category_summary,
    prompt_delete_transaction,
    prompt_export,
    prompt_list_transactions,
    prompt_monthly_summary,
    prompt_overall_stats,
    prompt_search,
)
from core.tracker import Tracker
from storage import persistence
from utils.exceptions import FinanceTrackerError, StorageError
 
 
def run() -> None:
    #   Creates a new Tracker instance. At this point it has empty lists/sets.
    #   This is the single object that holds ALL the application state during runtime.
    #   It gets passed around to every menu function that needs it.
    tracker = Tracker()
 
    #   Tries to load previously saved data from disk into the tracker.
    #   If the files don't exist or are corrupted (StorageError), we print a warning
    #   and continue with an empty tracker rather than crashing.
    try:
        persistence.load(tracker)
    except StorageError as e:
        print(f"  Warning: Could not load saved data — {e}")
    
    #   This is a DISPATCH TABLE (also called a command pattern).
    #   It's a dictionary where keys are menu choices (strings) and values are
    #   functions to call.
    dispatch = {
        "0": lambda: add_income_menu(tracker), 
        "1": lambda: add_expense_menu(tracker),
        "2": lambda: prompt_list_transactions(tracker),
        "3": lambda: prompt_search(tracker),
        "4": lambda: prompt_delete_transaction(tracker),
        "5": lambda: prompt_category_summary(tracker),
        "6": lambda: prompt_monthly_summary(tracker),
        "7": lambda: prompt_overall_stats(tracker),
        "8": lambda: prompt_budget_menu(tracker),
        "9": lambda: prompt_export(tracker),
        # exit with status code 0 —  conventionally means success
        "x": lambda: sys.exit(0),
    }
    #  'lambda: add_income_menu(tracker)' creates an anonymous function that takes
    #   no arguments and calls add_income_menu(tracker) when invoked.
    #   i used lambda instead of just add_income_menu
    #   Because add_income_menu needs the 'tracker' argument. If we wrote just
    #   add_income_menu, calling handler() would fail (missing argument).
    #   The lambda captures 'tracker' from the enclosing scope (closure).
    
    #  An infinite loop. The program keeps showing the menu and asking for input
    #  until the user exits
    while True:
        main_menu() # calls the function that prints the menu options to the screen.
        choice = input("  Your choice: ").strip() #input() reads a line of text the user types; .strip() removes leading/trailing whitespace (spaces, tabs, newlines).
 
        if choice == "x":
            print("\n  Goodbye!\n")
            sys.exit(0)
 
        handler = dispatch.get(choice) # look up the user's choice in the dispatch table. If the choice is valid, handler will be a function; if not, it safely return None and not raise KeyError.
        if handler: # none is falsy, so this checks if handler is not None 
            try:
                handler() # calls the function associated with the user's choice and main logic of each menu option gets executed.
            except FinanceTrackerError as e:
                print(f"\n  Error: {e}")
            except KeyboardInterrupt:
                print("\n  (interrupted)")
        else:
            print("  Invalid option — please enter a number from the menu.")
 
        input("\n  Press Enter to continue...") #  Pauses the loop and waits for the user to press Enter before showing the menu again.
 
if __name__ == "__main__":
    try: 
        run()
    except Exception as e:
        print(f"\n  ERROR: {e}")

#   __name__ is a special built-in variable.
#   When you run a file directly (python main.py), __name__ is set to "__main__".
#   When a file is imported by another file, __name__ is set to the module name.
#   So this block only runs when the file is the entry point, not when imported.
#   Basically we use it to hide tracebacks from users and print a clean error message 