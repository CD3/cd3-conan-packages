from pyparsing import *
import tempfile
import shutil
import subprocess
import util
import pathlib
import importlib
import inspect
import pprint

import util

import click



@click.command(help="Check all packages for newer upstream releases.")
def main():
  recipes = pathlib.Path("recipes").glob("*/conanfile.py")
  for recipe in recipes:
    conanfilename = str(recipe)
    spec = importlib.util.spec_from_file_location("conanfile", conanfilename)
    conanfile = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(conanfile)

    ConanPackage = get_conan_package_class(conanfile)


    name = ConanPackage.name
    current_version = ConanPackage.version
    git_url = get_git_url(ConanPackage)
    if git_url is None:
      print(f"No git url found for {name}. Skipping.")
      print()
      continue

    latest_version = util.get_latest_release(git_url,"master",None)

    print("Name:",name)
    print("Current Version:",current_version)
    print("Latest Version:",latest_version)
    print()

def get_conan_package_class(module):
  for item in dir(module):
    obj = getattr(module,item)
    if inspect.isclass(obj):
      for base in obj.__bases__:
        if base.__name__ == "ConanFile":
          return obj

def get_git_url(PackageClass):
  if 'git_url_basename' in PackageClass.__dict__:
    return f"{PackageClass.git_url_basename}/{PackageClass.name}"



if __name__ == "__main__":
  main()





