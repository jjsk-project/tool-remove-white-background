"""Pydantic V2 tool harness and CLI for threshold-based white removal."""
import argparse
import json
from time import perf_counter
from typing import Any, Callable, Type

from PIL import Image
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.config import BASE_DIR, INPUT_DIR, OUTPUT_DIR, SUPPORTED_EXTENSIONS
from src.database import is_processed
from src.utils import resolve_input


class RemoveWhiteBackgroundInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    file_name: str = Field(..., min_length=1, description="Image filename inside input/.")
    threshold: int = Field(default=240, ge=0, le=255, strict=True,
                           description="Make pixels transparent when all RGB channels are at least this value.")


def remove_white_background(file_name: str, threshold: int = 240) -> str:
    """Remove white and near-white pixels from an input image; save a transparent PNG and metadata in output/<stem>/."""
    started = perf_counter()
    try:
        args = RemoveWhiteBackgroundInput(file_name=file_name, threshold=threshold)
        source = resolve_input(args.file_name)
        folder = OUTPUT_DIR / source.stem
        folder.mkdir(parents=True, exist_ok=True)
        metadata_path = folder / "metadata.json"
        # Invalidate old completion state before attempting a new run.
        metadata_path.unlink(missing_ok=True)
        source_stat = source.stat()
        with Image.open(source) as original:
            image = original.convert("RGBA")
        pixels = list(image.getdata())
        removed = sum(r >= threshold and g >= threshold and b >= threshold for r, g, b, a in pixels)
        image.putdata([
            (255, 255, 255, 0) if r >= threshold and g >= threshold and b >= threshold else (r, g, b, a)
            for r, g, b, a in pixels
        ])
        artifact = folder / "transparent.png"
        image.save(artifact, "PNG")
        artifacts = [str(artifact.relative_to(BASE_DIR))]
        metadata = {
            "source_file": file_name, "status": "completed", "threshold": threshold,
            "source_size": source_stat.st_size, "source_mtime_ns": source_stat.st_mtime_ns,
            "output_directory": str(folder.relative_to(BASE_DIR)), "artifacts_created": artifacts,
            "width": image.width, "height": image.height, "pixels_matched": removed,
            "runtime_seconds": round(perf_counter() - started, 6),
        }
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return json.dumps({"status": "success", "output_folder": str(folder), "artifacts": artifacts,
                           "metadata": str(metadata_path.relative_to(BASE_DIR))})
    except Exception as exc:
        return json.dumps({"status": "error", "error_type": type(exc).__name__, "message": str(exc)})


class BaseTool:
    """Register a function schema and validate arguments at execution time."""
    def __init__(self, name: str, description: str, args_schema: Type[BaseModel], func: Callable[..., str]):
        self.name, self.description, self.args_schema, self.func = name, description, args_schema, func

    def to_openai_tool(self) -> dict[str, Any]:
        return {"type": "function", "function": {
            "name": self.name, "description": self.description,
            "parameters": self.args_schema.model_json_schema(),
        }}

    def run(self, **kwargs: Any) -> str:
        try:
            args = self.args_schema(**kwargs)
            return self.func(**args.model_dump())
        except ValidationError as exc:
            return json.dumps({"status": "validation_error", "message": "Invalid tool arguments.",
                               "details": json.loads(exc.json())})
        except Exception as exc:
            return json.dumps({"status": "error", "error_type": type(exc).__name__, "message": str(exc)})


remove_white_background_tool = BaseTool(
    "remove_white_background", remove_white_background.__doc__.strip(),
    RemoveWhiteBackgroundInput, remove_white_background,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--file", help="Filename inside input/.")
    mode.add_argument("--batch", action="store_true", help="Process unprocessed supported images.")
    mode.add_argument("--schema", action="store_true", help="Print the tool registration JSON.")
    parser.add_argument("--threshold", type=int, choices=range(256), default=240, metavar="0-255")
    parser.add_argument("--force", action="store_true", help="Reprocess completed files in batch mode.")
    args = parser.parse_args()
    if args.schema:
        print(json.dumps(remove_white_background_tool.to_openai_tool(), indent=2))
        return 0
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    names = [args.file] if args.file else sorted(
        p.name for p in INPUT_DIR.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    results = []
    for name in names:
        try:
            if args.batch and not args.force and is_processed(name, args.threshold):
                results.append({"status": "skipped", "file_name": name})
                continue
            result = json.loads(remove_white_background_tool.run(file_name=name, threshold=args.threshold))
        except Exception as exc:
            result = {"status": "error", "error_type": type(exc).__name__, "message": str(exc)}
        results.append({**result, "file_name": name})
    print(json.dumps(results if args.batch else results[0], indent=2))
    return int(any(r["status"] in {"error", "validation_error"} for r in results))


if __name__ == "__main__":
    raise SystemExit(main())
