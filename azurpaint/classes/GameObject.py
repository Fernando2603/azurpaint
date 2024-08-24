from __future__ import annotations

from PIL import Image
from typing import Generator, List, Optional, Union, cast
from UnityPy import classes
from UnityPy.enums import ClassIDType

from ..exception import \
  MeshImageNotFound, MonoBehaviourNotFound, RectTransformNotFound, TransformNotFound

from .AssetReader import AssetReader
from .MeshImage import MeshImage
from .RectTransform import RectTransform
from .Vector2 import Vector2



class GameObject:
  reader: AssetReader

  name: str
  path_id: int
  active: bool
  parent: Optional[GameObject]
  children: List[GameObject]

  # Unity component
  Transform: Union[classes.Transform, classes.RectTransform]
  RectTransform: Optional[RectTransform]
  MonoBehaviour: Optional[MeshImage]

  # variable
  scale: Vector2
  size: Vector2
  local_offset: Vector2
  global_offset: Vector2
  image: Optional[Image.Image]


  def __init__(
    self,
    reader: AssetReader,
    gameobject: classes.GameObject,
    parent: Optional[GameObject] = None
  ) -> None:
    self.reader = reader

    self.name = gameobject.name
    self.path_id = gameobject.path_id
    self.active = bool(gameobject.m_IsActive)
    self.parent = parent
    self.children = []

    # default value to prevent attr not found
    self.RectTransform = None
    self.MonoBehaviour = None
    self.image         = None
    self.scale         = Vector2.one()
    self.size          = Vector2.zero()
    self.local_offset  = Vector2.zero()
    self.global_offset = Vector2.zero()


    # this can be improved but im too lazy to change this
    self.Transform = cast(Union[classes.RectTransform, classes.Transform],
      self.reader.get_component_from_object(
        gameobject=gameobject,
        types=[ClassIDType.RectTransform, ClassIDType.Transform]
      )
    )

    if not self.Transform:
      # unexpected behaviour, since every component in unity
      # should have an Transform or RectTransform by default
      raise TransformNotFound(f"Transform not found in {self}.")

    if self.Transform.type == ClassIDType.RectTransform:
      self.RectTransform = RectTransform(cast(classes.RectTransform, self.Transform))

    # Transform have scale too
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

    # root always use size_delta when active
    # some root doesn't active like qiye_4 or kelifulan_4 it's gonna stretch the image
    # resize only smaller image than size delta
    # we handle image that larger in size delta in offset
    if (self.is_root and self.active) or size_delta.is_bigger(self.size):
      self.image = self.image.resize(size_delta.as_size(), Image.Resampling.LANCZOS)
      self.size = Vector2.from_value(self.image.size)
      return


  def __repr__(self) -> str:
    return f"<{self.__class__.__name__} name={self.name}>"


  @property
  def root(self) -> GameObject:
    root = self

    while self.parent:
      root = self.parent

    return root


  @property
  def is_root(self) -> bool:
    return bool(self.parent == None)


  def change_face(self, path_id: int) -> bool:
    if self.name != 'face':
      gameobject = self.root.find_child('face')

      # face should be available in all ship, even ship without face asset still have face gameobject
      if not gameobject:
        raise Exception(f"ERROR: {self.reader.prefab.as_posix()!r} <GameObject name=face> not found.")

      return gameobject.change_face(path_id=path_id)

    sprite: Optional[classes.Sprite] = self.reader.get_object_by_path_id(path_id=path_id)

    if not sprite:
      return False

    texture2d: classes.Texture2D = self.reader.get_object_by_path_id(
      path_id=sprite.m_RD.texture.path_id)

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


  def find_child(self, name: str) -> Optional[GameObject]:
    for child in self.children:
      if child.name == name:
        return child

      from_child = child.find_child(name)

      if from_child:
        return from_child


  def retrieve_children(self, recursive: bool = True) -> bool:
    if not self.Transform:
      return False

    for child in self.Transform.m_Children:
      child_transform = self.reader.get_object_by_path_id(child.path_id)
      child_object = self.reader.get_object_by_path_id(child_transform.m_GameObject.path_id)
      object_layer = GameObject(reader=self.reader, gameobject=child_object, parent=self)

      if recursive:
        object_layer.retrieve_children(recursive=recursive)
        self.children.append(object_layer)

    return True


  # todo: well move this method into RectTransform?
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

          # resize when local_offset already calculated to prevent miss calculation
          # self.size is the truesize, so size not updated here to make debug easier
          if self.image:
            self.image = self.image.resize(
              (self.size * self.scale).as_size(), Image.Resampling.LANCZOS)

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


  def calculate_global_offset(self, offset: Optional[Vector2] = None) -> Vector2:
    offset = offset or self.get_smallest_offset()

    self.global_offset = self.local_offset - offset

    for child in self.children:
      child.calculate_global_offset(offset=self.global_offset)

    return self.global_offset


  def get_biggset_size(self) -> Vector2:
    size_offset = Vector2.zero()

    if self.image:
      # we doesn't want to calculate root scale
      # dev sometimes put root scale into unreasonable value like 90x
      scale = Vector2.one() if self.is_root else self.scale
      size_offset = self.global_offset + (self.size * scale)

    for child in self.children:
      child_offset = child.get_biggset_size()
      size_offset = Vector2.max(size_offset, child_offset)

    return size_offset


  def yield_layers(self) -> Generator[GameObject, None, None]:
    if self.image:
      yield self

    for child in self.children:
      for layer in child.yield_layers():
        yield layer
