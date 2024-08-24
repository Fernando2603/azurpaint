class PrefabNotFound(Exception):
  """
    Custom class for AssetReader to identify if prefab not available in asset
  """


class MonoBehaviourNotFound(Exception):
  """
    Raised when MonoBehaviour not found.
  """


class MeshImageNotFound(Exception):
  """
    Raised when MeshImage not found in MonoBehaviour.
  """


class TransformNotFound(Exception):
  """
    Raised when GameObject doesn't have any Transform or RectTransform
  """


class RectTransformNotFound(Exception):
  """
    Raised when GameObject doesn't have RectTransform
  """
