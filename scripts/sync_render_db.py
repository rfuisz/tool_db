#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tool_db_backend.config import get_settings
from tool_db_backend.render_db_sync import RenderDbSyncError, sync_render_database


def main() -> int:
    try:
        result = sync_render_database(get_settings())
    except RenderDbSyncError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
