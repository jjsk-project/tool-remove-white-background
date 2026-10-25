# Execution contract

Register `main.remove_white_background_tool.to_openai_tool()` as a function tool and dispatch decoded arguments to `.run(**arguments)`. The function name is `remove_white_background`. Required argument: `file_name` (a top-level filename in input/); optional argument: `threshold` (integer 0–255, default 240). Unknown arguments are rejected.

Paths are relative to the project root, independent of the working directory. Traversal, absolute paths, and symlinks resolving outside input/ are rejected. Do not process multiple files with the same stem concurrently: their required output folder is shared. Execution is synchronous.

Success JSON contains `status`, `output_folder`, `artifacts`, and `metadata`. Metadata records completion status, source identity, parameters, dimensions, matched-pixel count, and elapsed seconds. Metadata is the persistence layer in src/database.py; successful completion is written only after the PNG is saved. IO and processing exceptions return JSON errors. Validation failures include structured Pydantic details.

`python main.py --batch` scans supported top-level images and skips completed items using metadata. `--force` overrides skips. CLI exit status is 1 if any item fails, otherwise 0. Empty batches return an empty array.

The original notebook's hardcoded Colab input path has been replaced with the validated input filename. Its inclusive RGB threshold and transparent-white replacement values are preserved. No network services are used.
