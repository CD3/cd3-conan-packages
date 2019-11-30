#! /usr/bin/python3
"""
Export conan packages to the local cache.

This script exports conan recipes to the local cache by default. Consumers
can then use the packages, but must specify `--build missing` the first time
they install.

If the --build option is given, then the packages will be built by calling `conan install`
after they are exported. In this case, consumers can use the package without specifying `--build missing`.

Package details (owner, channel, version, etc) have default values, but can be overriden with a YAML configuration
file. Use --print-default-configuration to see the default configuration values.

Here is an example configuration.

export-packages:
  packages_to_export: all
  scratch-folder: _package-exports.d
package_defaults:
  channel: devel
  checkout: master
  git_url_basename: git://github.com/CD3
  owner: cd3
  version: master
package_instances:
- baseline_conanfile: ./UnitConvert/conanfile.py
  checkout: 0.5.2
  name: UnitConvert
  version: 0.5.2

The `export-packages` section provides configuration parameters for this script.
The `package_defaults` section provides default values for each package.
The `package_instances` section provides overrides for each package.

Package configuration parameters:

  name  The package name.
  baseline_conanfile  A recipe file that will be used as a template for the package.
  git_url_basename  The git repository basename (git repo url minus the package name) were the package source can be downloaded.
  checkout  The git commit that should be checked out before building the package.
  version  The package version number.
  channel  The package channel.
  owner  The package owner.

This script will use the recipe specified by `baseline_conanfile` and inject configuration parameters to create
an instance conanfile.py that will be used to build the package. This means you can write a conanfile.py with default
values that will work on its own, and use this script to create different variations (obtain the source from a different repository, checkout
a different commit, etc).

The package references exported to the local cache will be '{name}/{version}@{owner}/{channel}'. By default, all packages will
be exported with the same owner and channel, but this can be overridden on a per-package basis. 

Usage:
  export-packages.py (-h|--help)
  export-packages.py [--package <name>]... [options] [<config_file> ...]
  export-packages.py [options] [<config_file> ...]

Options:
  -h,--help                       This help message.
  --print-default-configuration   Print the default configuration that will be used.
  --print-configuration           Print the actual configuration that will be used.
  -b,--build                      Build packages after they are installed.
  -t,--test                       Test package after it is installed.
  -n,--no-export                  Don't export packages. Can be used to skip export step and just build or test.
  -p <name>,--package <name>      Name of package(s) to export. This will override the list of packages specified in the config file.
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

  if args['--package']:
    packages_to_export = [ p.name for p in util.filter_packages( {'include' : args['--package'] }, pc.packages ) ]
  else:
    packages_to_export = [ p.name for p in util.filter_packages( pc.config[prog_path.stem].get('packages_to_test','all'), pc.packages ) ]

  if not args["--no-export"]:
    print("Exporting packages")
    with (Path(pc.config[prog_path.stem]["scratch-folder"]) / "conan_export.out" ).open('w') as f:
      pc.export_packages( config=packages_to_export, stdout = f)
    print("Done")

  if args["--build"]:
    print("Building packages")
    with (Path(pc.config[prog_path.stem]["scratch-folder"]) / "conan_build.out" ).open('w') as f:
      pc.build_packages( config=packages_to_export, stdout = f)
    print("Done")

  if args["--test"]:
    print("Testing packages")
    with (Path(pc.config[prog_path.stem]["scratch-folder"]) / "conan_test.out" ).open('w') as f:
      pc.test_packages( config=packages_to_export, stdout = f)
    print("Done")



