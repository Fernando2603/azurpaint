from pathlib import Path
from azurpaint import Azurpaint


def test():
  azurpaint = Azurpaint('AssetBundles', 'painting/tashigan')

  # check dependencies
  assert len(azurpaint.dependencies) == 1
  print(azurpaint.dependencies)

  # load dependencies (manual)
  azurpaint.load('painting/tashigan_tex')

  # search dependencies automatically within AssetBundles (root)
  # this is still in experimental mode so far on testing the result is good
  # load_dependencies only searching in local file and it doesn't know
  # if there any missing dependency it doesn't know what file it is
  # so you should provide complete asset include extracted OBB before running this
  azurpaint.load_dependencies()

  # check dependencies is not reliable but good to have
  # some asset require ui dependencies that just bloat
  assert azurpaint.check_dependency()

  target = Path(Path(__file__).parent, 'output')
  target.mkdir(parents=True, exist_ok=True)

  # create an image
  azurpaint.create(
    trim=True,      # remove unused transparent box, this will reduce the image size
    downscale=True  # downscale image to 2048x2048 if image is larger
  ).save(Path(target, 'tashkent.png'))

  # change face expression
  print(azurpaint.face_list)
  for face in azurpaint.face_list:
    azurpaint.change_face(face)
    azurpaint.create().save(Path(target, f"tashkent-expression-{face}.png"))


if __name__ == '__main__':
  test()