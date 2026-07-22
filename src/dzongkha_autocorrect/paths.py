from __future__ import annotations

import os
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_DB_PATH = Path(
    os.environ.get("DZA_DB_PATH", str(_REPO_ROOT / "data" / "dzongkha.db"))
)
