from __future__ import annotations

import re

from PIL import Image
from typing import Dict, Optional, cast
from UnityPy import classes
from UnityPy.enums import ClassIDType

from ..exception import MeshImageNotFound, MonoBehaviourNotFound

from .AABB import AABB
from .AssetReader import AssetReader
from .Vector2 import Vector2


VR = re.compile(r'v ')
TR = re.compile(r'vt ')
SR = re.compile(r' ')


class MeshImage:
  reader: AssetReader

  MonoBehaviour: classes.MonoBehaviour
  Sprite: Optional[classes.Sprite]
  Mesh: Optional[classes.Mesh]
  image: Optional[Image.Image]


  def __init__(self, reader: AssetReader, gameobject: classes.GameObject) -> None:
    self.reader = reader
    self.MonoBehaviour = self.reader.get_component_from_object(
      gameobject=gameobject, types=[ClassIDType.MonoBehaviour], attributes={'mMesh'})

    if not self.MonoBehaviour:
      raise MonoBehaviourNotFound(f"MonoBehaviour not found in <GameObject name={gameobject.name}>")

    script_name = self.MonoBehaviour.m_Script.read().name

    if script_name not in ['MeshImage', 'Image']:
      raise MeshImageNotFound(f"MeshImage not found in <GameObject name={gameobject.name}>.")

    # default value
    self.Sprite = None
    self.Mesh   = None
    self.image  = None

    if gameobject.name == 'face':
      self.load_face(expression='0')
      return

    self.Sprite = self.load_sprite()

    if not self.Sprite:
      return

    self.Mesh = self.load_mesh()

    texture2d: classes.Texture2D = self.reader.get_object_by_path_id(
      path_id=self.Sprite.m_RD.texture.path_id)

    self.image = texture2d.image

    if self.Mesh:
      self.image = self.reconstruct_image_mesh(image=self.image, mesh=self.Mesh)

    self.image = self.recalculate_image_size(image=self.image)


  def __repr__(self) -> str:
    image = 'image' if self.image else ''
    mode = f"mode={self.image.mode}" if self.image else ''
    size = 'x'.join([str(x) for x in self.size.as_size()])
    mesh = 'mesh' if self.Mesh else ''
    return f"<{self.__class__.__name__} {mesh} {image} {mode} size={size}>"


  @property
  def path_id(self) -> Optional[int]:
    return self.MonoBehaviour.path_id if self.MonoBehaviour else None


  @property
  def size(self) -> Vector2:
    return Vector2.from_value(self.image.size) if self.image else Vector2.zero()


  @property
  def AABB(self) -> AABB:
    center = Vector2.zero()
    extend = Vector2.zero()

    if self.Mesh:
      center = Vector2.from_value(self.Mesh.m_LocalAABB.m_Center)
      extend = Vector2.from_value(self.Mesh.m_LocalAABB.m_Extent)

    return AABB(center=center, extend=extend)


  @property
  def mRawSpriteSize(self) -> Optional[Vector2]:
    if self.MonoBehaviour and hasattr(self.MonoBehaviour, 'mRawSpriteSize'):
      return Vector2.from_value(
        list(cast(Dict[str, int], self.MonoBehaviour.mRawSpriteSize).values()))


  def load_sprite(self) -> Optional[classes.Sprite]:
    if not hasattr(self.MonoBehaviour, 'm_Sprite'):
      return None

    if not isinstance(self.MonoBehaviour.m_Sprite, classes.PPtr):
      return None

    sprite = self.reader.get_object_by_path_id(path_id=self.MonoBehaviour.m_Sprite.path_id)

    if sprite and (sprite.name.lower() != 'uisprite'):
      return sprite


  def load_mesh(self) -> Optional[classes.Mesh]:
    if not hasattr(self.MonoBehaviour, 'mMesh'):
      return None

    if not isinstance(self.MonoBehaviour.mMesh, classes.PPtr):
      return None

    return self.reader.get_object_by_path_id(path_id=self.MonoBehaviour.mMesh.path_id)


  def load_face(self, expression: str) -> Optional[classes.Sprite]:
    self.Sprite: Optional[classes.Sprite] = self.reader.get_object_by_name(
      name=expression, type=ClassIDType.Sprite)

    if self.Sprite:
      texture2d: classes.Texture2D = self.reader.get_object_by_path_id(
        path_id=self.Sprite.m_RD.texture.path_id)

      self.image = texture2d.image

    return self.Sprite


  def reconstruct_image_mesh(self, image: Image.Image, mesh: classes.Mesh) -> Image.Image:
    image_size = Vector2.from_value(image.size)
    mesh_object = mesh.export().splitlines()

    coordinates = map(SR.split, list(filter(TR.match, mesh_object))[1::2])
    points = map(SR.split, list(filter(VR.match, mesh_object))[1::2])

    coordinates = [
      (round(float(a[1]) * image_size.x), round((1 - float(a[2])) * image_size.y))
      for a in coordinates
    ]

    points = [(-int(float(a[1])), int(float(a[2]))) for a in points]
    max_py = max(y for _, y in points)
    points = [(x, max_py - y) for x, y in points[::2]]

    combined = [
      (left + right, point)
      for left, right, point in zip(coordinates[::2], coordinates[1::2], points)
    ]

    output_x, output_y = zip(*[
      (right - left + px, bottom - top + py)
      for (left, top, right, bottom), (px, py) in combined
    ])

    output_size = (max(output_x), max(output_y) + int(self.AABB.padding.y))
    output_image = Image.new('RGBA', output_size, (0, 0, 0, 0))

    for crop_box, paste_point in combined:
      output_image.paste(image.crop(crop_box), (paste_point))

    return output_image


  def recalculate_image_size(self, image: Image.Image) -> Image.Image:
    raw_size = self.mRawSpriteSize

    if not raw_size:
      return image

    image_size = Vector2.from_value(image.size)

    if image_size != raw_size:
      image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

      c_size = Vector2.max(image_size, raw_size).as_size()
      canvas = Image.new('RGBA', c_size, (0, 0, 0, 0))
      canvas.paste(image)

      image = canvas.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

    return image
