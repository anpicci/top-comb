
from pathlib import Path
# ============================================================
# Utility Functions
# ============================================================
def write_text(path: Path, text: str) -> None:
    """
    Write text to file with error handling.
    """
    try:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(text)
    except IOError as e:
        raise IOError(f"Failed to write to {path}: {e}") from e

