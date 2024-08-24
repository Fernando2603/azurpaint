from __future__ import annotations

from PIL import Image
from typing import Dict, Iterable, List, Union
from pathlib import Path


from .classes import AssetReader, GameObject
from .types import PathLike


class Azurpaint:
  path: Path
  prefab: Path
  reader: AssetReader


  def __init__(self, path: PathLike, prefab: PathLike) -> None:
    self.path = Path(path)
    self.prefab = Path(prefab)
    self.reader = AssetReader(path=path, prefab=prefab)


  def __repr__(self) -> str:
    return f"<{self.__class__.__name__} prefab={self.prefab.as_posix()!r}>"


  @property
  def face(self) -> Dict[str, int]:
    return self.reader.face


  @property
  def face_list(self) -> List[str]:
    return list(self.face.keys())


  @property
  def files(self) -> List[str]:
    return self.reader.files


  @property
  def cabs(self) -> List[str]:
    return self.reader.cabs


  @property
  def dependencies(self) -> List[str]:
    return self.reader.dependencies


  @property
  def gameobject(self) -> GameObject:
    if not hasattr(self, '_gameobject'):
      self._gameobject = GameObject(self.reader, self.reader.root)
      self._gameobject.retrieve_children()
      self._gameobject.calculate_local_offset()
      self._gameobject.calculate_global_offset()

    return self._gameobject


  def load_dependencies(self, force_face_load: bool = True) -> None:
    """
      Automatically search for dependencies by name.

      :params force_face_load: force load face with matching name

      Warning
      -------
      This is still in experimental state, undefined behaviour may occurs.
    """
    return self.reader.load_dependencies(force_face_load=force_face_load)
  

  def check_dependency(self) -> bool:
    """
      Check if dependency is fully loaded or not

      this is not reliable at all since the game use dependency file to determine it.
    """
    return all(dependency in self.cabs for dependency in self.dependencies)


  def change_face(self, expression: str) -> bool:
    if not len(self.face):
      print(f"Prefab {self.prefab.as_posix()!r} paintingface is not loaded.")
      return False

    if expression not in self.face:
      if expression == '0':
        del self._gameobject
        self.gameobject # re-render
        return True

      print(f"Face not found, available option is {list(self.face.keys())}.")
      return False

    if not self.gameobject.change_face(path_id=self.face[expression]):
      return False

    self.gameobject.calculate_local_offset()
    self.gameobject.calculate_global_offset()
    return True


  def load(self, path: Union[PathLike, Iterable[PathLike]]) -> List[Path]:
    return self.reader.loads(path)


  def create(self, trim: bool = True, downscale: bool = True) -> Image.Image:
    gameobject = self.gameobject

    canvas_size = gameobject.get_biggset_size().as_size()
    canvas = Image.new('RGBA', canvas_size, (0, 0, 0, 0))

    for layer in gameobject.yield_layers():
      if layer.image:
        canvas.alpha_composite(layer.image, layer.global_offset.as_size())

    if trim:
      canvas = canvas.crop(canvas.getbbox())

    if downscale and ((canvas.size[0] > 2048) or (canvas.size[1] > 2048)):
      sizex, sizey = canvas.size

      if sizex > sizey:
        return canvas.resize((2048, round((2048 / sizex) * sizey)), Image.Resampling.LANCZOS)

      return canvas.resize((round((2048 / sizey) * sizex), 2048), Image.Resampling.LANCZOS)

    return canvas

