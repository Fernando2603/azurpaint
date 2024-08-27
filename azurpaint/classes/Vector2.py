from __future__ import annotations

from math import inf
from typing import Any, Callable, Union
from UnityPy import math


class Vector2:
  x: float
  y: float

  def __init__(self, x: Union[int, float], y: Union[int, float]) -> None:
    if not self._typecheck(x):
      raise TypeError(
        f"Invalid type for {self.__class__.__name__}.x: '{type(x)}', expected int or float.")

    if not self._typecheck(y):
      raise TypeError(
        f"Invalid type for {self.__class__.__name__}.y: '{type(y)}', expected int or float.")

    self.x = float(x)
    self.y = float(y)


  def __add__(self, value: Any) -> Vector2:
    if not isinstance(value, Vector2):
      value = Vector2.from_value(value)

    return Vector2(self.x + value.x, self.y + value.y)


  def __sub__(self, value: Any) -> Vector2:
    if not isinstance(value, Vector2):
      value = Vector2.from_value(value)

    return Vector2(self.x - value.x, self.y - value.y)


  def __mul__(self, value: Any) -> Vector2:
    if not isinstance(value, Vector2):
      value = Vector2.from_value(value)

    return Vector2(self.x * value.x, self.y * value.y)


  def __truediv__(self, value: Any) -> Vector2:
    if not isinstance(value, Vector2):
      value = Vector2.from_value(value)

    return Vector2(self.x / value.x, self.y / value.y)


  def __floordiv__(self, value: Any) -> Vector2:
    if not isinstance(value, Vector2):
      value = Vector2.from_value(value)

    return Vector2(self.x // value.x, self.y // value.y)


  def __eq__(self, value: Any) -> bool:
    if not isinstance(value, Vector2):
      try:
        value = Vector2.from_value(value) # pyright: ignore
      except:
        return False

    distance = (self - value)
    epsilon2 = (0.00001 * 0.00001)
    return epsilon2 > sum((distance * distance).values())


  def __ne__(self, value: Any) -> bool:
    return not self.__eq__(value)


  def __repr__(self) -> str:
    return f"<{self.__class__.__name__} x={self.x} y={self.y}>"


  def values(self) -> tuple[float, float]:
    return (self.x, self.y)


  def as_size(self) -> tuple[int, int]:
    """
      Easy size convertion for pillow usage.

      `as_int` is not picked because `as_size` is more intuitive
      since it truncate the `float`, also the output is `tuple[int, int]`
    """
    return (int(self.x), int(self.y))


  def apply(self, func: Callable[[float], float]) -> Vector2:
    """
      Apply an function to each axis, this will modify the `Vector2`.
    """
    self.x = func(self.x)
    self.y = func(self.y)
    return self


  def is_bigger(self, value: Any) -> bool:
    """
      Check if both axis is bigger or equal than other but not equal on both axis.
    """
    if not isinstance(value, Vector2):
      value = Vector2.from_value(value)

    if self == value:
      return False

    return (self.x >= value.x) and (self.y >= value.y)


  @staticmethod
  def _typecheck(value: Any) -> bool:
    """
      Pyright suck on isinstance so this is required
    """
    if isinstance(value, (int, float)):
      return True

    if isinstance(value, str):
      try:
        float(value)
        return True

      except:
        return False

    return False


  @staticmethod
  def from_value(value: Any) -> Vector2:
    """
      Convert any value into `Vector2` if requirement is meet.

      ```Python
        Vector2             # return itself (references)
        int                 # return x and y with same value (cast to float)
        float               # return x and y with same value
        tuple               # require atleast 2 length of int or float value
        list                # require atleast 2 length of int or float value
        object              # require x or y key (non sensitive case)
        UnityPy.Vector2     # converted 
        UnityPy.Vector3     # converted drop Z
        Unitypy.Quarternion # converted drop Z and W
      ```
    """
    if isinstance(value, Vector2):
      return value

    if isinstance(value, (int, float)):
      return Vector2(x=value, y=value)

    # UnityPy Vector and Quaternion
    if isinstance(value, (math.Vector2, math.Vector3, math.Quaternion)):
      return Vector2(x=value.X, y=value.Y)

    # overflow are ignored
    if isinstance(value, (tuple, list)):
      if len(value) < 2:
        raise ValueError(f"{type(value).__name__.title()} value minimal should have 2 length.")

      return Vector2(x=value[0], y=value[1])

    # any class or object that have x and y value
    has_x = hasattr(value, 'x') or hasattr(value, 'X') or ('x' in value) or ('X' in value)
    has_y = hasattr(value, 'y') or hasattr(value, 'Y') or ('y' in value) or ('Y' in value)

    if not has_x or not has_y:
      raise ValueError(f"'{value}' cannot be converted into Vector2.")

    if isinstance(value, dict):
      value_x = value.get('x', value.get('X', None))
      value_y = value.get('y', value.get('Y', None))
    else:
      value_x = getattr(value, 'x', getattr(value, 'X', None))
      value_y = getattr(value, 'y', getattr(value, 'Y', None))

    if value_x == None: raise ValueError("value 'x' is None, expected int or float.")
    if value_y == None: raise ValueError("value 'y' is None, expected int or float.")

    return Vector2(x=value_x, y=value_y)


  @staticmethod
  def max(*args: Vector2) -> Vector2:
    """
      :return: new `Vector2` with maximum value in input
    """
    max_x = -inf
    max_y = -inf

    for vector in args:
      if vector.x > max_x: max_x = vector.x
      if vector.y > max_y: max_y = vector.y

    return Vector2(x=max_x, y=max_y)


  @staticmethod
  def min(*args: Vector2) -> Vector2:
    """
      :return: new `Vector2` with minimum value in input
    """
    min_x = inf
    min_y = inf

    for vector in args:
      if vector.x < min_x: min_x = vector.x
      if vector.y < min_y: min_y = vector.y

    return Vector2(x=min_x, y=min_y)


  @staticmethod
  def zero() -> Vector2:
    """
      :return: `Vector2(x=0, y=0)`
    """
    return Vector2(x=0, y=0)


  @staticmethod
  def one() -> Vector2:
    """
      :return: `Vector2(x=1, y=1)`
    """
    return Vector2(x=1, y=1)
