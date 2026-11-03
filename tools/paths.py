"""Project and work paths shared by the editing tools."""
import os
from pathlib import Path


def project_root():
    """Use CLAUDE_EDIT_ROOT, otherwise the folder above tools/."""
    value = os.environ.get("CLAUDE_EDIT_ROOT", "").strip()
    return Path(value).expanduser().resolve() if value else Path(__file__).resolve().parent.parent


def work_folder(edit_id=None, *parts):
    """Return work/ or a folder inside it, without creating anything."""
    base = (project_root() / "work").resolve()
    result = base.joinpath(*(() if edit_id is None else (str(edit_id),)), *map(str, parts)).resolve()
    if not result.is_relative_to(base):
        raise ValueError("work folder must stay inside the project's work/")
    return result


ROOT = project_root()
