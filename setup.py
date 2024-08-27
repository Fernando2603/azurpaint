from setuptools import setup, find_packages

setup(
  name='azurpaint',
  version='1.0.0',
  packages=find_packages(),
  python_requires='>=3.9',
  install_requires=['UnityPy', 'Pillow']
)