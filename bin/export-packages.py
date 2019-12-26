#! /usr/bin/python3
import shutil
import sys
import yaml
from pathlib import Path

import util

import click


prog_path = Path(sys.argv[0]).resolve()
@click.command()
@click.option("--print-default-configuration", help ="Print the default configuration that will be used and exit.",is_flag=True)
@click.option("--print-configuration",         help ="Print the actual configuration that will be used and exit.", is_flag=True)
@click.option("-p","--package",                help ="Select subset of packages to export.",multiple=True)
@click.option("-o","--owner",                  help ="Set owner to to use for package export.",default="cd3")
@click.option("-c","--channel",                help ="Set channel to to use for package export.",default="devel")
@click.option("--create",                      help ="Create packages (build and pacakage) instead of just exporting.",is_flag=True)
@click.argument("config_file", required=False, nargs=-1, type=click.Path())
def main(print_default_configuration,print_configuration,package,owner,channel,create,config_file):
  """
  Export conan packages to the local cache.

  This script exports conan recipes to the local cache by default. Consumers
  can then use the packages, but must specify `--build missing` the first time
  they install.
  """

  pc = util.PackageCollection()
  default_configuration_file = prog_path.parent / f"{prog_path.stem}-default-config.yaml"
  if default_configuration_file.exists():
    default_configuration_text = default_configuration_file.read_text()
  else:
    default_configuration_text = ""
    print(util.WARN + f"WARNING: did not find default configuration file '{str(default_configuration_file)}'." + util.EOL)
  pc.load( yaml.load( default_configuration_text, Loader=yaml.SafeLoader ) )
  if print_default_configuration:
    print("# Default Configuration")
    print(yaml.dump(pc.config))
    sys.exit(0)

  for file in config_file:
    pc.update( yaml.load( Path(file).read_text(), Loader=yaml.SafeLoader ) )

  if not 'package_instances' in pc.config:
    pc.add_from_conan_recipe_collection("recipes")

  if print_configuration:
    print("# Complete Configuration")
    print(yaml.dump(pc.config))
    sys.exit(0)

  scratch_folder_path = Path(pc.config[prog_path.stem]["scratch-folder"])
  if scratch_folder_path.exists():
    shutil.rmtree(str(scratch_folder_path))
  scratch_folder_path.mkdir()

  if package:
    packages_to_export = [ p.name for p in util.filter_packages( {'include' : list(package) }, pc.package_instances ) ]
  else:
    packages_to_export = [ p.name for p in util.filter_packages( pc.config[prog_path.stem].get('packages_to_test','all'), pc.package_instances ) ]

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
