from __future__ import annotations

from os import PathLike as _PathLike
from typing import Union
from pathlib import Path


PathLike = Union[Path, _PathLike[str], str]
"""
  Extended `os.PathLike` type to include `pathlib.Path` and literal string
"""


