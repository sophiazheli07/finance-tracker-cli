import json
from datetime import datetime
from pathlib import Path

from core.tracker import Tracker
from reports.analytics import category_breakdown, overall_stats
EXPORTS_DIR = Path("exports") # Exports go in a separate folder, not mixed with data files.

def export_path(name: str, ext: str) -> Path:
    EXPORTS_DIR.mkdir(parents = True, exist_ok = True) # create folder if does not exist, do now throw error if exists
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") # current date and time
    return EXPORTS_DIR / f"{name}_{timestamp}.{ext}"

#json

def export_transactions_json(tracker: Tracker) -> Path:
    """export all transactions to a json file, return path"""
    path = export_path("transactions", "json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump( # export a dict with metadata and list of transactions converted to dicts (since JSON can't serialize Transaction objects directly)
            {
                "exported_at": datetime.now().isoformat(),
                "transactions": [t.to_dict() for t in tracker.transactions],
            },
            f,# write to file
            indent = 2, # pretty print with 2 spaces
            ensure_ascii = False, # allow non-ASCII characters in the output (e.g. for merchant names in different languages)
        )
    return path

def export_full_report_json(tracker: Tracker) -> Path:
    """export overall status summary to json, return path"""
    path = export_path("overall_status", "json")
    with open(path, "w", encoding="utf-8") as f: # w - write mode (overwrites existing file or creates new one if it doesn't exist) and specify UTF-8 encoding for consistency across systems
        json.dump(
            {
                "exported_at": datetime.now().isoformat(),
                "overall_status": overall_stats(tracker),
                "category_breakdown": category_breakdown(tracker),
            },
            f,# write to file
            indent=2, # pretty print with 2 spaces
            ensure_ascii=False, # allow non-ASCII characters in the output (e.g. for merchant names in different languages)
        )

    return path