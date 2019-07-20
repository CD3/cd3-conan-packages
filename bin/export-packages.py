#! /usr/bin/python3

import glob
import os
import subprocess
import multiprocessing
import shutil
import sys
import yaml
from pathlib import Path

import util

from argparse import ArgumentParser

parser = ArgumentParser(description="Export conan packages to the local cache. Does not perform any testing.")
parser.add_argument(
    "configuration",
    action="store",
    nargs='*',
    help="File contianing configurations to export.")
parser.add_argument(
    "--print-default-configuration",
    action='store_true',
    help="Print the default configuration.")
parser.add_argument(
    "--print-configuration",
    action='store_true',
    help="Print the configuration that will be used..")
parser.set_defaults(parallel=True)
args = parser.parse_args()

prog_path = Path(parser.prog)


package_paths = [Path(file).parent for file in Path.cwd().glob("*/conanfile.py")]
if __name__ == '__main__':

  pc = util.PackageCollection()
  default_configuration_text = f'''
package_defaults:
  version: master
  channel: devel
  owner: cd3
  git_url_basename: git://github.com/CD3
  checkout: master
{prog_path.stem}:
  packages_to_export : all
  scratch-folder : "_package-exports.d"
'''
  pc.load( yaml.load( default_configuration_text, Loader=yaml.SafeLoader ) )
  if args.print_default_configuration:
    print("# Default Configuration")
    print(yaml.dump(pc.config))
    sys.exit(0)

  for file in args.configuration:
    pc.update( yaml.load( Path(file).read_text(), Loader=yaml.SafeLoader ) )

  if not 'package_instances' in pc.config:
    pc.add_from_conan_recipe_collection(".")

  if args.print_configuration:
    print("# Complete Configuration")
    print(yaml.dump(pc.config))
    sys.exit(0)

  scratch_folder_path = Path(pc.config[prog_path.stem]["scratch-folder"])
  if scratch_folder_path.exists():
    shutil.rmtree(str(scratch_folder_path))
  scratch_folder_path.mkdir()


  print("Exporting packages")
  with (Path(pc.config[prog_path.stem]["scratch-folder"]) / "conan_export.out" ).open('w') as f:
    pc.export_packages( config=pc.config[prog_path.stem].get("packages_to_export", "all"), stdout = f)
  print("Done")




