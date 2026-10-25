"""Metadata-based state tracking; no separate database is required."""
import json
from .config import OUTPUT_DIR


def is_processed(file_name: str, threshold: int) -> bool:
    from .utils import resolve_input
    source = resolve_input(file_name)
    folder = OUTPUT_DIR / source.stem
    try:
        metadata = json.loads((folder / "metadata.json").read_text())
        return (
            metadata.get("status") == "completed"
            and metadata.get("source_file") == file_name
            and metadata.get("source_size") == source.stat().st_size
            and metadata.get("source_mtime_ns") == source.stat().st_mtime_ns
            and metadata.get("threshold") == threshold
            and (folder / "transparent.png").is_file()
        )
    except (OSError, ValueError, TypeError):
        return False
