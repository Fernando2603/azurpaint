from __future__ import annotations

from UnityPy import classes

from .Vector2 import Vector2


class RectTransform:
  """
    Converted UnityPy RectTransform with Vector2 only.
  """
  path_id: int
  anchor_min: Vector2
  anchor_max: Vector2
  anchor_pos: Vector2
  size_delta: Vector2
  local_scale: Vector2
  pivot: Vector2


  def __init__(self, rtf: classes.RectTransform) -> None:
    self.path_id = rtf.path_id
    self.anchor_min = Vector2.from_value(rtf.m_AnchorMin)
    self.anchor_max = Vector2.from_value(rtf.m_AnchorMax)
    self.anchor_pos = Vector2.from_value(rtf.m_AnchoredPosition)
    self.size_delta = Vector2.from_value(rtf.m_SizeDelta)
    self.local_scale = Vector2.from_value(rtf.m_LocalScale)
    self.pivot = Vector2.from_value(rtf.m_Pivot)


  def __repr__(self) -> str:
    return f"<{self.__class__.__name__} path_id={self.path_id}>"
