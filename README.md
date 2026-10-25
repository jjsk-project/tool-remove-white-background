# Remove white background

Converted from `tool_remove_white_background_py.ipynb` to the Pydantic V2 file-processing template. Requires Python 3.10+.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Place images in input/ first.
python main.py --file example.jpg
python main.py --batch
python main.py --batch --threshold 250 --force
python main.py --schema
```

Each image produces `output/<image_stem>/transparent.png` and `metadata.json`. Use distinct filename stems: `photo.jpg` and `photo.png` share an output folder. Supported extensions: PNG, JPG/JPEG, WebP, BMP, TIF/TIFF. For animated or multipage images, only the first frame is processed.

A pixel becomes transparent when **all three** RGB channels are greater than or equal to the threshold (default 240). Other pixels retain their original RGBA values. This removes matching pixels anywhere in the image, including white foreground details; it does not detect object boundaries.

Batch mode skips files with matching successful metadata, source size/modification time, threshold, and an existing output PNG. Use `--force` to regenerate them. Input files are preserved. Failures return JSON and a nonzero CLI exit code.

## Tool calls

```python
import json
from main import remove_white_background_tool

registration = remove_white_background_tool.to_openai_tool()
result = json.loads(remove_white_background_tool.run(file_name="example.jpg", threshold=240))
```

The harness uses `model_json_schema()` for registration and validates calls with Pydantic V2. No API credentials or model SDK are needed. Invalid arguments return `status: validation_error`; processing failures return `status: error`.
