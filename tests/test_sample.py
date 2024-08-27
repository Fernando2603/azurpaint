from pathlib import Path
from azurpaint import Azurpaint
from azurpaint.classes import Vector2

ASSET_BUNDLES = Path(Path(__file__).parent, 'AssetBundles')
PREFAB = 'painting/tashigan'


def test_load_dependencies():
  az = Azurpaint(ASSET_BUNDLES, PREFAB)

  assert len(az.dependencies) == 1
  az.load_dependencies()

  # load _tex and paintingface
  assert len(az.files) == 3


def test_single_extract():
  az = Azurpaint(ASSET_BUNDLES, PREFAB)
  az.load_dependencies()
  az.create()


def test_change_face():
  az = Azurpaint(ASSET_BUNDLES, PREFAB)
  az.load_dependencies()

  for face in az.face_list:
    az.change_face(face)
    az.create()


def test_vector2():
  assert Vector2.zero().values() == (0.0, 0.0)
  assert Vector2.one().values() == (1.0, 1.0)

  Vector2.from_value(Vector2.zero())
  Vector2.from_value(1)
  Vector2.from_value(2.0)
  Vector2.from_value((3.0, 4.0))
  Vector2.from_value([5.0, 6.0])
  Vector2.from_value({ 'x': 1, 'y': 2 })

  class test_object_static:
    x = 1
    y = 1

  Vector2.from_value(test_object_static)

  class test_object_dynamic:
    def __init__(self, x, y):
      self.x = x
      self.y = y

  Vector2.from_value(test_object_dynamic(1, 0))

  # test operator
  vx, vy = (5, 5)

  vt1 = Vector2(vx, vy)
  vt2 = Vector2(vx, vy)
  vt3 = Vector2(vx - vx, vy - vy)
  vt4 = Vector2(vx + vx, vy + vy)
  vt5 = Vector2(vx * vx, vy * vy)
  vt6 = Vector2(vx / vx, vy / vy)

  assert (vt1 - vt2) == vt3
  assert (vt1 + vt2) == vt4
  assert (vt1 * vt2) == vt5
  assert (vt1 / vt2) == vt6

  # test method
  assert Vector2.min(vt3, vt4) == vt3
  assert Vector2.max(vt3, vt4) == vt4

  assert Vector2(-1.5, -5.5).apply(abs) == Vector2(1.5, 5.5)
  assert vt4.is_bigger(vt3)

  assert vt1.as_size() == (int(vx), int(vy))
  assert vt1.values() == (float(vx), float(vy))
