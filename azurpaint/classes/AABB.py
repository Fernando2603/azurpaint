from __future__ import annotations

from .Vector2 import Vector2


class AABB:
  center: Vector2
  extend: Vector2

  def __init__(self, center: Vector2, extend: Vector2) -> None:
    self.center = center
    self.extend = extend


  def __repr__(self) -> str:
    return f"<{self.__class__.__name__} center={self.center.values()} extend={self.extend.values()}>"


  @property
  def padding(self) -> Vector2:
    return self.center - self.extend


  @property
  def size(self) -> Vector2:
    return self.center + self.extend
