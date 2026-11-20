import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULE_VERSION = "1.1.0"
MAX_RECORDS = 3000
MAX_YEAR_SPAN = 12
SAMPLES = {"clean": "验收清册", "dirty": "十一月补刊清单", "renewal": "续订改版清册"}


def database_path():
    return Path(os.environ.get("SERIAL_LEDGER_DB", ROOT / "instance" / "ledger.sqlite3"))
