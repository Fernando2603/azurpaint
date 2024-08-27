# azurpaint

[![PyPI supported Python versions](https://img.shields.io/pypi/pyversions/azurpaint.svg)](https://pypi.python.org/pypi/azurpaint)
[![MIT](https://img.shields.io/github/license/Fernando2603/azurpaint)](https://github.com/Fernando2603/azurpaint/blob/main/LICENSE)


Azur Lane painting reconstructor/extractor.

## Install
**Python 3.9.0 or higher is required**
```cmd
pip install azurpaint
```

## Usage

Simple example to extract painting

- create new folder
- get and extract `/Android/obb/com.YoStarEN.AzurLane/*.obb` to new folder
- copy `AssetBundles` from `/Android/data/com.YoStarEN.AzurLane/files/AssetBundles`

> [!NOTE]
> only `painting`, `paintings` and `paintingface` folder are required from `AssetBundles`.


```Python
from pathlib import Path
from azurpaint import Azurpaint
from azurpaint.exception import PrefabNotFound

# extract painting with default expression/face
def extract(asset_bundle_path, prefab_path):
  try:
    azurpaint = Azurpaint(asset_bundle_path, prefab_path)

    # search dependencies automatically within AssetBundles (root)
    # this is still in experimental mode so far on testing the result is good
    # load_dependencies only searching in local file and it doesn't know
    # if there any missing dependency it doesn't know what file it is
    # so you should provide complete asset include extracted OBB before running this
    azurpaint.load_dependencies()

    # PIL.Image.Image
    return azurpaint.create()
  except PrefabNotFound:
    print(f"{prefab_path} is not an prefab.")


# extract painting with all face/expression into output_dir
def extract_all_face(asset_bundle_path, prefab_path, output_dir):
  try:
    azurpaint = Azurpaint(asset_bundle_path, prefab_path)
    azurpaint.load_dependencies()

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    azurpaint.create().save(Path(output_dir, f"{azurpaint.prefab.name}-default.png"))

    for face in azurpaint.face_list:
      azurpaint.change_face(face)
      azurpaint.create().save(Path(output_dir, f"{azurpaint.prefab.name}-{face}.png"))

  except PrefabNotFound:
    print(f"{prefab_path} is not an prefab.")


if __name__ == '__main__':
  # azurpaint require asset that have .prefab
  # will raise PrefabNotFound if file is not an prefab
  extract('path_to/AssetBundles', 'painting/tashigan')
```
