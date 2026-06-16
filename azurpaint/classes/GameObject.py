from collections.abc import Generator
from typing import cast

from PIL import Image
from UnityPy.classes import GameObject as UnityGameObject
from UnityPy.classes import RectTransform as UnityRectTransform
from UnityPy.classes import Sprite, Texture2D
from UnityPy.classes import Transform as UnityTransform
from UnityPy.enums import ClassIDType

from ..exception import (
  MeshImageNotFound,
  MonoBehaviourNotFound,
  RectTransformNotFound,
  TransformNotFound,
)
from .AssetReader import AssetReader
from .MeshImage import MeshImage
from .RectTransform import RectTransform as TypeRectTransform
from .Vector2 import Vector2


class GameObject:
  reader: AssetReader

  name: str
  path_id: int
  active: bool
  parent: "GameObject | None"
  children: list["GameObject"]

  # Unity component
  Transform: UnityTransform | UnityRectTransform
  RectTransform: TypeRectTransform | None
  MonoBehaviour: MeshImage | None

  # variable
  scale: Vector2
  size: Vector2
  local_offset: Vector2
  global_offset: Vector2
  image: Image.Image | None

  def __init__(
    self,
    reader: AssetReader,
    gameobject: UnityGameObject,
    parent: "GameObject | None" = None,
  ) -> None:
    self.reader = reader

    self.name = gameobject.m_Name
    self.path_id = getattr(gameobject, "path_id", -1)
    self.active = bool(gameobject.m_IsActive)
    self.parent = parent
    self.children = []

    # default value to prevent attr not found
    self.RectTransform = None
    self.MonoBehaviour = None
    self.image = None
    self.scale = Vector2.one()
    self.size = Vector2.zero()
    self.local_offset = Vector2.zero()
    self.global_offset = Vector2.zero()

    self.Transform = cast(
      UnityRectTransform | UnityTransform,
      self.reader.get_component_from_object(
        gameobject=gameobject, types=[ClassIDType.RectTransform, ClassIDType.Transform]
      ),
    )

    if not self.Transform:
      raise TransformNotFound(f"Transform not found in {self}.")

    if isinstance(self.Transform, UnityRectTransform):
      self.RectTransform = TypeRectTransform(self.Transform)

    self.scale = Vector2.from_value(self.Transform.m_LocalScale)

    if self.parent and not self.parent.is_root:
      self.scale *= self.parent.scale

    if not (self.is_root or self.active):
      return

    try:
      self.MonoBehaviour = MeshImage(self.reader, gameobject=gameobject)

      if self.is_root or self.active:
        self.image = self.MonoBehaviour.image

      if self.image:
        self.size = Vector2.from_value(self.image.size)

    except (MeshImageNotFound, MonoBehaviourNotFound):
      pass

    if not self.image:
      return

    if not self.RectTransform:
      raise RectTransformNotFound(f"RectTransform not found in {self}.")

    size_delta = self.RectTransform.size_delta

    if (self.is_root and self.active) or size_delta.is_bigger(self.size):
      self.image = self.image.resize(size_delta.as_size(), Image.Resampling.LANCZOS)
      self.size = Vector2.from_value(self.image.size)
      return

  def __repr__(self) -> str:
    return f"<{self.__class__.__name__} name={self.name}>"

  @property
  def root(self) -> "GameObject":
    root = self

    while self.parent:
      root = self.parent

    return root

  @property
  def is_root(self) -> bool:
    return bool(self.parent is None)

  def change_face(self, path_id: int) -> bool:
    if self.name != "face":
      gameobject = self.root.find_child("face")

      if not gameobject:
        raise Exception(
          f"ERROR: {self.reader.prefab.as_posix()!r} <GameObject name=face> not found."
        )

      return gameobject.change_face(path_id=path_id)

    sprite: Sprite | None = self.reader.get_object_by_path_id(path_id=path_id)

    if not sprite:
      return False

    texture_reader = sprite.m_RD.texture.deref()

    if not texture_reader:
      return False

    texture2d = cast(Texture2D, texture_reader.parse_as_object())

    self.active = True
    self.image = texture2d.image
    self.size = Vector2.from_value(self.image.size)

    if not self.RectTransform:
      raise RectTransformNotFound(f"RectTransform not found in {self}.")

    size_delta = self.RectTransform.size_delta

    if size_delta.is_bigger(self.size):
      self.image = self.image.resize(size_delta.as_size(), Image.Resampling.LANCZOS)
      self.size = Vector2.from_value(self.image.size)

    return True

  def find_child(self, name: str) -> "GameObject | None":
    for child in self.children:
      if child.name == name:
        return child

      from_child = child.find_child(name)
      if from_child:
        return from_child

  def retrieve_children(self, recursive: bool = True) -> bool:
    if not self.Transform or not self.Transform.m_Children:
      return False

    for child in self.Transform.m_Children:
      child_transform_reader = child.deref()

      if not child_transform_reader:
        continue

      child_transform = child_transform_reader.parse_as_object()
      child_object_reader = child_transform.m_GameObject.deref()

      if not child_object_reader:
        continue

      child_object = child_object_reader.parse_as_object()
      object_layer = GameObject(
        reader=self.reader,
        gameobject=child_object,  # type: ignore
        parent=self,
      )

      if recursive:
        object_layer.retrieve_children(recursive=recursive)
        self.children.append(object_layer)

    return True

  def calculate_local_offset(self, recursive: bool = True) -> Vector2:
    if self.RectTransform:
      anchor_min = self.RectTransform.anchor_min
      anchor_max = self.RectTransform.anchor_max
      anchor_pos = self.RectTransform.anchor_pos
      size_delta = self.RectTransform.size_delta
      pivot = self.RectTransform.pivot

      if anchor_min == anchor_max:
        if self.parent:
          pivot = Vector2(x=pivot.x, y=1 - pivot.y)

          pivot_offset = (pivot * size_delta) + (0, self.size.y - size_delta.y)
          pivot_anchor = self.scale * pivot_offset

          anchor_offset = Vector2(x=anchor_pos.x - pivot_anchor.x, y=anchor_pos.y + pivot_anchor.y)
          self.local_offset = (self.parent.size * anchor_min) + (anchor_offset.x, -anchor_offset.y)

          if self.image:
            self.image = self.image.resize(
              (self.size * self.scale).as_size(), Image.Resampling.LANCZOS
            )

      else:
        if self.parent:
          self.size = self.parent.size * (anchor_min - anchor_max).apply(abs)

        self.local_offset = Vector2(x=-anchor_pos.x, y=anchor_pos.y)

    if recursive:
      for child in self.children:
        child.calculate_local_offset(recursive=recursive)

    return self.local_offset

  def get_smallest_offset(self) -> Vector2:
    min_offset = Vector2.zero()

    if self.image:
      min_offset = self.local_offset

    for child in self.children:
      child_offset = child.get_smallest_offset()
      min_offset = Vector2.min(min_offset, child_offset)

    return min_offset

  def calculate_global_offset(self, offset: Vector2 | None = None) -> Vector2:
    offset = offset or self.get_smallest_offset()

    self.global_offset = self.local_offset - offset

    for child in self.children:
      child.calculate_global_offset(offset=self.global_offset)

    return self.global_offset

  def get_biggset_size(self) -> Vector2:
    size_offset = Vector2.zero()

    if self.image:
      scale = Vector2.one() if self.is_root else self.scale
      size_offset = self.global_offset + (self.size * scale)

    for child in self.children:
      child_offset = child.get_biggset_size()
      size_offset = Vector2.max(size_offset, child_offset)

    return size_offset

  def yield_layers(self) -> Generator["GameObject", None, None]:
    if self.image:
      yield self

    for child in self.children:
      yield from child.yield_layers()
