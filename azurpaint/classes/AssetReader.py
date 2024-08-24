from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Union, cast
from pathlib import Path
from UnityPy import Environment, classes
from UnityPy.enums import ClassIDType
from UnityPy.files import ObjectReader

from ..types import PathLike
from ..exception import PrefabNotFound


class AssetReader:
  """
    Read UnityAsset using UnityPy.
  """
  path: Path
  prefab: Path
  environment: Environment
  files: List[str] = []
  face: Dict[str, int]

  def __init__(self, path: PathLike, prefab: PathLike) -> None:
    self.face = {}
    self.path = Path(path)
    self.prefab = Path(prefab)

    if not self.filepath.exists():
      raise FileNotFoundError(f"File {self.filepath.as_posix()!r} not exists.")

    self.environment = Environment(self.filepath.as_posix())
    self.files.append(self.prefab.as_posix())

    if not self.has_prefab:
      raise PrefabNotFound(f"Prefab {self.prefab.as_posix()!r} not exists.")


  def __repr__(self) -> str:
    return f"<{self.__class__.__name__} prefab={self.prefab.as_posix()}>"


  @property
  def root(self) -> classes.GameObject:
    return self.get_object_by_path_id(next(iter(self.environment.container.values())).path_id)


  @property
  def filepath(self) -> Path:
    return Path(self.path, self.prefab)


  @property
  def has_prefab(self) -> bool:
    try:
      return any(key.endswith('.prefab') for key in self.environment.container.keys())
    except:
      return False


  @property
  def cabs(self) -> List[str]:
    return list(k for k in self.environment.cabs.keys() if not k.endswith('.ress'))


  @property
  def dependencies(self) -> List[str]:
    assets: classes.AssetBundle = self.get_object_by_path_id(1)
    
    if not hasattr(assets, 'm_Dependencies'):
      raise ValueError(f"Prefab {self.prefab.as_posix()} is missing 'AssetBundle.m_Dependencies'.")

    return cast(List[str], assets.m_Dependencies)


  def get_cabs(self, name: PathLike) -> List[str]:
    environment = Environment(Path(name).as_posix())
    return list(k for k in environment.cabs.keys() if not k.endswith('.ress'))


  def load(self, path: PathLike, is_face: bool = False) -> Path:
    path = Path(path)

    if not path.is_relative_to(self.path):
      path = Path(self.path, path)

    # is_dependencies is not used, it's a bit complicated with azurlane assets
    # since some asset like paintingface is not an direct dependency for a lot ship
    self.environment.load_file(path.as_posix())
    self.files.append(path.relative_to(self.path).as_posix())

    if is_face or path.is_relative_to(Path(self.path, 'paintingface')):
      self.face = self._get_face(path)

    return path


  def loads(self, path: Union[PathLike, Iterable[PathLike]]) -> List[Path]:
    if not isinstance(path, Iterable) or isinstance(path, str):
      path = [path]

    _loaded = []

    for link in path:
      _loaded.append(self.load(link))

    return _loaded


  def _gather_files(self, folders: List[str] = ['painting', 'paintings', 'paintingface']) -> List[str]:
    """
      Get all files list that have same name as prefab in painting, paintings and paintingface
    """
    files: List[str] = []

    for folder in folders:
      glob = Path(self.path, folder).glob(f"{self.prefab.name.split('_')[0]}*")
      files.extend([file.relative_to(self.path).as_posix() for file in glob])

    return files


  def _get_face(self, path: Path) -> Dict[str, int]:
    face = {}

    for obj in cast(List[ObjectReader], self.environment.files[path.as_posix()].get_objects()):
      if obj.type != ClassIDType.Sprite:
        continue

      obj = cast(classes.Sprite, obj.read())
      face[obj.name] = obj.path_id

    return {key: face[key] for key in sorted(face.keys())}



  def _load_face(self, force: bool = True) -> None:
    if len(self.face):
      return

    files = self._gather_files(['paintingface'])
    prefab_face = Path('paintingface', self.prefab.name).as_posix()

    if prefab_face in files:
      self.load(prefab_face, is_face=True)
      return

    if not force:
      return

    # face not found or not same as prefab name
    # sometimes face have different name with underscore extension 
    # but still have same basename eg like _hx extension
    # this is not perfect it may load wrong face
    possible_name: List[str] = [prefab_face]

    while '_' in prefab_face:
      prefab_face = prefab_face.rsplit('_', 1)[0]
      possible_name.append(prefab_face)

    matches: List[str] = [file for file in files if file in possible_name]

    if len(matches) == 0:
      return

    # when matches is more than one. probably the longest is more desired one
    # since it splitted with underscore so we're prefer longer string
    self.load(max(matches, key=len), is_face=True)


  def find_dependencies(self) -> Tuple[Set[str], Set[str]]:
    """
      Find all dependencies in loaded path

      :returns: tuple[`result`, `missing_dependencies`]
    """
    result: Set[str] = set()
    dependencies: Set[str] = set(self.dependencies)

    if not len(dependencies):
      return result, dependencies

    files: List[str] = self._gather_files()

    # blank image used by asset to create canvas
    files.append('painting/touming_tex')

    for file in files:
      if not len(dependencies):
        break

      for cab in self.get_cabs(Path(self.path, file)):
        if cab in dependencies:
          result.add(file)
          dependencies.remove(cab)

    return result, dependencies


  def load_dependencies(self, force_face_load: bool = False) -> None:
    """
      Automatically search for dependencies by name.

      :params force_face_load: force load face with matching name

      Warning
      -------
      This is still in experimental state, undefined behaviour may occurs.
    """
    dependencies, _ = self.find_dependencies()

    if not len(self.face):
      self._load_face(force=force_face_load)

    self.loads(dependencies)


  def get_object_by_path_id(self, path_id: int) -> Any:
    for obj in self.environment.objects:
      if obj.path_id == path_id:
        return cast(Any, obj.read(return_typetree_on_error=False))


  def get_object_by_name(self, name: str, type: ClassIDType) -> Any:
    for obj in self.environment.objects:
      try:
        if not hasattr(obj, 'name') or (obj.type != type):
          continue

        obj = cast(Any, obj.read(return_typetree_on_error=False))

        if hasattr(obj, 'name') and (str(obj.name) == str(name)):
          return obj

      except:
        continue


  def get_component_from_object(
    self,
    gameobject: classes.GameObject,
    types: Optional[Iterable[ClassIDType]] = None,
    names: Optional[Set[str]] = None,
    attributes: Optional[Set[str]] = None
  ) -> Any:
    for component_pptr in cast(List[classes.PPtr], gameobject.m_Components):
      if types and (not component_pptr.type in types):
        continue

      component = self.get_object_by_path_id(component_pptr.path_id)

      if names and (not component.name in names):
        continue

      if attributes:
        for attribute in attributes:
          if hasattr(component, attribute):
            return component

      return component
