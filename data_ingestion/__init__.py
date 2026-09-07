from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parent.parent
for _pkg in (_REPO_ROOT / "packages").glob("*/src"):
    if str(_pkg) not in sys.path:
        sys.path.insert(0, str(_pkg))

__version__ = "0.1.0"
