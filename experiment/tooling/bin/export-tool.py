#! /usr/bin/python3
import shutil
import sys
import yaml
import pprint
from pathlib import Path

import util

import click


prog_path = Path(sys.argv[0]).resolve()
@click.command()
@click.option("--print-default-configuration", help ="Print the default configuration that will be used and exit.",is_flag=True)
@click.option("--print-configuration",         help ="Print the actual configuration that will be used and exit.", is_flag=True)
@click.option("-p","--packages",               help ="Comma-separated list of packages to export.")
@click.option("-o","--owner",                  help ="Set owner to to use for package export.")
@click.option("-c","--channel",                help ="Set channel to to use for package export.")
@click.option("--create",                      help ="Create packages (build and pacakage) instead of just exporting.",is_flag=True)
@click.argument("config_file", required=False, nargs=-1, type=click.Path())
def main(print_default_configuration,print_configuration,packages,owner,channel,create,config_file):
  """
  Export conan packages to the local cache.

  This script exports conan recipes to the local cache by default. Consumers
  can then use the packages, but must specify `--build missing` the first time
  they install.

  This script allows conan package recipes to be generated from a base recipe. For example, if you wanted to create
  a package for the last three major releases of LibA, the recipe files for each version would probably look identical
  expect for the version number and the commit that gets checked out (unless the build system changes). Rather than
  write three different recipes, you can just write a single recipe for the latest release. This script can then
  generate recipes for the other versions.

  To do this, every package that gets exported by this script starts with a
  base recipe. You can then specify settings to override (see Configuration
  Settings below) to create a new recipe instance. If no override settings are
  specified, then the recipe instance will just be the base recipe.

        base recipe -> [override settigns] -> recipe instance

  This is convenient because it allows you to maintain a collection of valid
  recipe files that can be tested and used with just conan, and then use this
  script to export variations on these recipes.
  

  Configuration:

  The exported packages can be configured using a YAML file and passing it as an argument to this script.

  Configuration Settings:

  \b
  global
      a namespace for global package settings (setting that will be applied to all packages)
  global.export
      a namespace for setting related to exporting packages.
  global.export.owner
      the default package owner
  global.export.channel
      the default package channel
  package_instances
      a namespace used for overriding package settings on a per-package basis.
  package_instances[i].conanfile
      path to the conan recipe to use.
  package_instances[i].name
      name used to refer to package in the script.
      this is not the name that will be used in the package recipe (see settings_overrides)
  package_instances[i].setting_overrides
      a dict of key/value pairs that will be added to the recipe instance to override settings in the base recipe.
      the key/value pairs are arbitrary. if the key is a setting in the base recipe, it will be overridden. if it is
      not, it will be added.
  package_instances[i].setting_overrides.name
      override the package name
  package_instances[i].setting_overrides.version
      override the package version
  package_instances[i].setting_overrides.checkout
      override the git reference that will be checked out to build the package. must be supported by the base recipe.
  export-tool
      a namespace used for setting for this script
  export-tool.scratch-folder
      the name of the directory used for writing data to disk (logs, temp files, etc)
  export-tool.packages_to_export
      a list of packages to export. by default, all packages will be exported.
      this will be overridden by the --packages option.

  Example Configuration File:

  \b
  export-packages:
    packages_to_export: all
    scratch-folder: _package-exports.d
  global:
    export:
      channel: devel
      owner: MyOrg
  package_instances:
  - conanfile: /path/to/LibA/conanfile.py
    name: LibA
    setting_overrides:
      version: "3.1"
      checkout: "v3.1"
  - conanfile: /path/to/LibA/conanfile.py
    name: LibA
    setting_overrides:
      version: "3.2"
      checkout: "v3.2"

  This will create and export a recipe instance for every conanfile.py found in the recipies directory,
  and two recipe instances for the LibA package.
  """

  default_configuration_file = prog_path.parent / f"{prog_path.stem}-default-config.yaml"
  if default_configuration_file.exists():
    default_configuration_text = default_configuration_file.read_text()
  else:
    default_configuration_text = ""
    print(util.WARN + f"WARNING: did not find default configuration file '{str(default_configuration_file)}'." + util.EOL)


  config = yaml.load( default_configuration_text, Loader=yaml.BaseLoader )
  if print_default_configuration:
    print("# Default Configuration")
    print(yaml.dump(config))
    sys.exit(0)

  for file in config_file:
    util.update_dict( config, yaml.load( Path(file).read_text(), Loader=yaml.BaseLoader ) )

  
  if not 'global' in config:
    config['global'] = dict()

  if not 'export' in config['global']:
    config['global']['export'] = dict()

  if owner:
    config['global']['export']['owner'] = owner
  if channel:
    config['global']['export']['channel'] = channel

  if packages:
    if packages in ['all','instances-only']:
      config[prog_path.stem]['packages_to_export'] = packages
    else:
      config[prog_path.stem]['packages_to_export'] = packages.split(",")

  packages_to_export = config[prog_path.stem].get('packages_to_export','all')



  if not 'package_instances' in config:
    config['package_instances'] = list()

  # sort of a hack. we want to let the user specify that only the instances explicitly listed
  # should be exported
  if packages_to_export != "instances-only":
    for file in Path("recipes").glob("*/conanfile.py"):
      config['package_instances'].append( {'conanfile':str(file.absolute()), 'name' : str(file.parent.stem) } )
    for file in Path("recipes").glob("*/conanfile-latest.py"):
      config['package_instances'].append( {'conanfile':str(file.absolute()), 'name' : str(file.parent.stem) } )
  else:
    packages_to_export = "all"

  # make sure all conanfiles are specified with absolute path
  for instance in config["package_instances"]:
    instance["conanfile"] = str(Path(instance["conanfile"]).absolute())

  if print_configuration:
    print("# Complete Configuration")
    print(yaml.dump(config))
    sys.exit(0)

  pc = util.PackageCollection()
  pc.load( config )

  scratch_folder_path = Path(pc.config[prog_path.stem]["scratch-folder"])
  if scratch_folder_path.exists():
    shutil.rmtree(str(scratch_folder_path))
  scratch_folder_path.mkdir()

  packages_to_export = [ p.name for p in util.filter_packages( packages_to_export, pc.package_instances ) ]

  if create:
    print("Creating packages")
    with (Path(pc.config[prog_path.stem]["scratch-folder"]) / "conan_export.out" ).open('w') as f:
      pc.create_packages( config=packages_to_export, stdout = f)
    print("Done")
  else:
    print("Exporting packages")
    with (Path(pc.config[prog_path.stem]["scratch-folder"]) / "conan_export.out" ).open('w') as f:
      pc.export_packages( config=packages_to_export, stdout = f)
    print("Done")




if __name__ == '__main__':
  main()
