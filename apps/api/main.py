from pathlib import Path
import sys

import uvicorn

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tool_db_backend.api import app


def run() -> None:
    uvicorn.run("apps.api.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    run()
