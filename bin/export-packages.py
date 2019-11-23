#! /usr/bin/python3
"""
Export conan packages to the local cache.

Usage:
  export-packages.py [options] [<config_file> ...]
  export-packages.py (-h|--help)

Options:
  -h,--help                       This help message.
  --print-default-configuration   Print the default configuration that will be used.
  --print-configuration           Print the actual configuration that will be used.
  -b,--build                      Build packages after they are installed.
  -t,--test                       Test package after it is installed.
  -n,--no-export                  Don't export packages. Can be used to skip export step and just build or test.
"""
import docopt
args = docopt.docopt( __doc__ )

import glob
import os
import subprocess
import multiprocessing
import shutil
import sys
import yaml
from pathlib import Path

import util


prog_path = Path(sys.argv[0]).resolve()


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
  if args['--print-default-configuration']:
    print("# Default Configuration")
    print(yaml.dump(pc.config))
    sys.exit(0)

  for file in args['<config_file>']:
    pc.update( yaml.load( Path(file).read_text(), Loader=yaml.SafeLoader ) )

  if not 'package_instances' in pc.config:
    pc.add_from_conan_recipe_collection(".")

  if args['--print-configuration']:
    print("# Complete Configuration")
    print(yaml.dump(pc.config))
    sys.exit(0)

  scratch_folder_path = Path(pc.config[prog_path.stem]["scratch-folder"])
  if scratch_folder_path.exists():
    shutil.rmtree(str(scratch_folder_path))
  scratch_folder_path.mkdir()


  if not args["--no-export"]:
    print("Exporting packages")
    with (Path(pc.config[prog_path.stem]["scratch-folder"]) / "conan_export.out" ).open('w') as f:
      pc.export_packages( config=pc.config[prog_path.stem].get("packages_to_export", "all"), stdout = f)
    print("Done")

  if args["--build"]:
    print("Building packages")
    with (Path(pc.config[prog_path.stem]["scratch-folder"]) / "conan_build.out" ).open('w') as f:
      pc.build_packages( config=pc.config[prog_path.stem].get("packages_to_export", "all"), stdout = f)
    print("Done")

  if args["--test"]:
    print("Testing packages")
    with (Path(pc.config[prog_path.stem]["scratch-folder"]) / "conan_test.out" ).open('w') as f:
      pc.test_packages( config=pc.config[prog_path.stem].get("packages_to_export", "all"), stdout = f)
    print("Done")



