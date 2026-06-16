from os import PathLike as _PathLike
from pathlib import Path

PathLike = Path | _PathLike[str] | str
"""
  Extended `os.PathLike` type to include `pathlib.Path` and literal string
"""
