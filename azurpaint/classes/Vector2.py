from collections.abc import Callable
from math import inf
from typing import Any

TYPE_CHECK_MESSAGE = "Invalid type for {name}.x: '{type}', expected int, float, or parseable str."


class Vector2:
  x: float
  y: float

  def __init__(self, x: int | float | str, y: int | float | str) -> None:
    if not self._typecheck(x):
      raise TypeError(TYPE_CHECK_MESSAGE.format(name=self.__class__.__name__, type=type(x)))

    if not self._typecheck(y):
      raise TypeError(TYPE_CHECK_MESSAGE.format(name=self.__class__.__name__, type=type(y)))

    self.x = float(x)
    self.y = float(y)

  def __add__(self, value: Any) -> "Vector2":
    if not isinstance(value, Vector2):
      value = Vector2.from_value(value)

    return Vector2(self.x + value.x, self.y + value.y)

  def __sub__(self, value: Any) -> "Vector2":
    if not isinstance(value, Vector2):
      value = Vector2.from_value(value)

    return Vector2(self.x - value.x, self.y - value.y)

  def __mul__(self, value: Any) -> "Vector2":
    if not isinstance(value, Vector2):
      value = Vector2.from_value(value)

    return Vector2(self.x * value.x, self.y * value.y)

  def __truediv__(self, value: Any) -> "Vector2":
    if not isinstance(value, Vector2):
      value = Vector2.from_value(value)

    return Vector2(self.x / value.x, self.y / value.y)

  def __floordiv__(self, value: Any) -> "Vector2":
    if not isinstance(value, Vector2):
      value = Vector2.from_value(value)

    return Vector2(self.x // value.x, self.y // value.y)

  def __eq__(self, value: Any) -> bool:
    if not isinstance(value, Vector2):
      try:
        value = Vector2.from_value(value)
      except Exception:
        return False

    distance = self - value
    epsilon2 = 0.00001 * 0.00001
    return epsilon2 > sum((distance * distance).values())

  def __ne__(self, value: Any) -> bool:
    return not self.__eq__(value)

  def __repr__(self) -> str:
    return f"<{self.__class__.__name__} x={self.x} y={self.y}>"

  def values(self) -> tuple[float, float]:
    return (self.x, self.y)

  def as_size(self) -> tuple[int, int]:
    """
    Easy size conversion for pillow usage.
    """
    return (int(self.x), int(self.y))

  def apply(self, func: Callable[[float], float]) -> "Vector2":
    """
    Apply a function to each axis, modifying the instance coordinates.
    """
    self.x = func(self.x)
    self.y = func(self.y)
    return self

  def is_bigger(self, value: Any) -> bool:
    """
    Check if both axes are bigger or equal than other but not identical on both axes.
    """
    if not isinstance(value, Vector2):
      value = Vector2.from_value(value)

    if self == value:
      return False

    return (self.x >= value.x) and (self.y >= value.y)

  @staticmethod
  def _typecheck(value: Any) -> bool:
    if isinstance(value, (int, float)):
      return True

    if isinstance(value, str):
      try:
        float(value)
        return True
      except Exception:
        return False

    return False

  @staticmethod
  def from_value(value: Any) -> "Vector2":
    """
    Convert structural data types into a Vector2 mapping.
    """
    if isinstance(value, Vector2):
      return value

    if isinstance(value, (int, float)):
      return Vector2(x=value, y=value)

    if isinstance(value, (tuple, list)):
      if len(value) < 2:  # type: ignore
        raise ValueError(f"{type(value).__name__} value minimal should have 2 length.")  # type:ignore

      return Vector2(x=value[0], y=value[1])  # type: ignore

    if isinstance(value, dict):
      value_x = value.get("x", value.get("X", None))  # type: ignore
      value_y = value.get("y", value.get("Y", None))  # type: ignore
    else:
      value_x = getattr(value, "x", getattr(value, "X", None))
      value_y = getattr(value, "y", getattr(value, "Y", None))

    if value_x is None or value_y is None:
      raise ValueError(f"'{value}' cannot be safely converted into a Vector2 structure.")

    return Vector2(x=value_x, y=value_y)  # type: ignore

  @staticmethod
  def max(*args: "Vector2") -> "Vector2":
    max_x = -inf
    max_y = -inf

    for vector in args:
      if vector.x > max_x:
        max_x = vector.x
      if vector.y > max_y:
        max_y = vector.y

    return Vector2(x=max_x, y=max_y)

  @staticmethod
  def min(*args: "Vector2") -> "Vector2":
    min_x = inf
    min_y = inf

    for vector in args:
      if vector.x < min_x:
        min_x = vector.x
      if vector.y < min_y:
        min_y = vector.y

    return Vector2(x=min_x, y=min_y)

  @staticmethod
  def zero() -> "Vector2":
    return Vector2(x=0, y=0)

  @staticmethod
  def one() -> "Vector2":
    return Vector2(x=1, y=1)
