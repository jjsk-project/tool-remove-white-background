from pathlib import Path
from .config import INPUT_DIR, SUPPORTED_EXTENSIONS


def resolve_input(file_name: str) -> Path:
    """Resolve a top-level input filename without allowing directory traversal."""
    if not file_name or Path(file_name).name != file_name or file_name in {".", ".."}:
        raise ValueError("file_name must be a filename directly inside input/.")
    path = INPUT_DIR / file_name
    if path.resolve().parent != INPUT_DIR.resolve():
        raise ValueError("Input symlinks must resolve inside input/.")
    if not path.is_file():
        raise FileNotFoundError(f"Input file '{file_name}' not found in {INPUT_DIR}")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported image extension: {path.suffix}")
    return path
