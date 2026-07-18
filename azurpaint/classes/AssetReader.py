from collections.abc import Iterable
from pathlib import Path
from typing import Any, cast

from UnityPy import Environment, classes
from UnityPy.enums import ClassIDType
from UnityPy.files import ObjectReader

from ..exception import PrefabNotFound
from ..types import PathLike


class AssetReader:
  """
  Read UnityAsset using modern UnityPy
  """

  path: Path
  prefab: Path
  environment: Environment
  files: list[str]
  face: dict[str, int]

  def __init__(self, path: PathLike, prefab: PathLike) -> None:
    self.files = []
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
    if hasattr(self, "_root"):
      return self._root

    for obj in cast(list[ObjectReader[Any]], self.environment.objects):
      if obj.type != ClassIDType.GameObject:
        continue

      if obj.peek_name().lower() != self.prefab.stem.lower():  # type: ignore
        continue

      gameobject = cast(classes.GameObject, obj.parse_as_object())
      component = self.get_component_from_object(
        gameobject=gameobject, types=[ClassIDType.RectTransform, ClassIDType.Transform]
      )

      if not component:
        continue

      parent_ptr = getattr(component, "m_Father", None)
      if (parent_ptr is None) or (parent_ptr.path_id == 0):
        self._root = gameobject
        return gameobject

    raise RuntimeError("Root gameobject not found")

  @property
  def filepath(self) -> Path:
    return Path(self.path, self.prefab)

  @property
  def has_prefab(self) -> bool:
    try:
      return any(key.endswith(".prefab") for key in self.environment.container)
    except Exception:
      return False

  @property
  def cabs(self) -> list[str]:
    return [k for k in self.environment.cabs if not k.endswith(".ress")]

  @property
  def dependencies(self) -> list[str]:
    assets: classes.AssetBundle = self.get_object_by_path_id(1)

    if not hasattr(assets, "m_Dependencies"):
      raise ValueError(f"Prefab {self.prefab.as_posix()} is missing 'AssetBundle.m_Dependencies'.")

    return cast(list[str], assets.m_Dependencies)

  def get_cabs(self, name: PathLike) -> list[str]:
    environment = Environment(Path(name).as_posix())
    return [k for k in environment.cabs if not k.endswith(".ress")]

  def load(self, path: PathLike, is_face: bool = False) -> Path:
    path = Path(path)

    if not path.is_relative_to(self.path):
      path = Path(self.path, path)

    # is_dependencies is not used, it's a bit complicated with azurlane assets
    # since some asset like paintingface is not an direct dependency for a lot ship
    self.environment.load_file(path.as_posix())
    self.files.append(path.relative_to(self.path).as_posix())

    if is_face or path.is_relative_to(Path(self.path, "paintingface")):
      self.face = self._get_face(path)

    return path

  def loads(self, path: PathLike | Iterable[PathLike]) -> list[Path]:
    if not isinstance(path, Iterable) or isinstance(path, str):
      path = [path]

    return [self.load(link) for link in path]

  def _gather_files(self, folders: list[str] | None = None) -> list[str]:
    """
    Get all files list that have same name as prefab in painting, paintings and paintingface
    """
    if folders is None:
      folders = ["painting", "paintings", "paintingface"]

    files: list[str] = []

    for folder in folders:
      glob = Path(self.path, folder).glob(f"{self.prefab.name.split('_')[0]}*")
      files.extend([file.relative_to(self.path).as_posix() for file in glob])

    return files

  def _get_face(self, path: Path) -> dict[str, int]:
    face: dict[str, int] = {}

    for obj in cast(list[ObjectReader[Any]], self.environment.objects):
      if obj.type != ClassIDType.Sprite:
        continue

      obj = cast(ObjectReader[classes.Sprite], obj)

      if obj.assets_file and (obj.assets_file.name == path.name):  # type: ignore
        sprite_obj = obj.parse_as_object()
        face[sprite_obj.m_Name] = obj.path_id

    return {key: face[key] for key in sorted(face.keys())}

  def _load_face(self, force: bool = True) -> None:
    if len(self.face):
      return

    files = self._gather_files(["paintingface"])
    prefab_face = Path("paintingface", self.prefab.name).as_posix()

    if prefab_face in files:
      self.load(prefab_face, is_face=True)
      return

    if not force:
      return

    possible_name: list[str] = [prefab_face]

    while "_" in prefab_face:
      prefab_face = prefab_face.rsplit("_", 1)[0]
      possible_name.append(prefab_face)

    matches: list[str] = [file for file in files if file in possible_name]

    if len(matches) == 0:
      return

    self.load(max(matches, key=len), is_face=True)

  def find_dependencies(self) -> tuple[set[str], set[str]]:
    """
    Find all dependencies in loaded path

    :returns: tuple[`result`, `missing_dependencies`]
    """
    result: set[str] = set()
    dependencies: set[str] = set(self.dependencies)

    if not len(dependencies):
      return result, dependencies

    files: list[str] = self._gather_files()
    files.append("painting/touming_tex")

    for file in files:
      if not len(dependencies):
        break

      for cab in self.get_cabs(Path(self.path, file)):
        if cab in dependencies:
          result.add(file)
          dependencies.remove(cab)

    return result, dependencies

  def load_dependencies(self, force_face_load: bool = False) -> None:
    dependencies, _ = self.find_dependencies()

    if not len(self.face):
      self._load_face(force=force_face_load)

    self.loads(dependencies)

  def get_object_by_path_id(self, path_id: int) -> Any:
    for obj in cast(list[ObjectReader[Any]], self.environment.objects):
      if obj.path_id == path_id:
        return obj.parse_as_object()

  def get_object_by_name(self, name: str, type: ClassIDType) -> Any:
    for obj in cast(list[ObjectReader[Any]], self.environment.objects):
      try:
        if obj.type != type:
          continue

        if obj.peek_name() == name:
          return obj.parse_as_object()

      except Exception:
        continue

  def get_component_from_object(
    self,
    gameobject: classes.GameObject,
    types: Iterable[ClassIDType] | None = None,
    names: set[str] | None = None,
    attributes: set[str] | None = None,
  ) -> Any:
    for component_pptr in cast(list[classes.PPtr[Any]], gameobject.m_Components):
      if types and (component_pptr.type not in types):
        continue

      reader = component_pptr.deref()
      component = reader.parse_as_object()

      if names and (getattr(component, "m_Name", None) not in names):
        continue

      if attributes:
        for attribute in attributes:
          if hasattr(component, attribute):
            return component

      return component
