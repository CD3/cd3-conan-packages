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
    "--parallel",
    dest='parallel',
    action='store_true',
    help="Run jobs in parallel")
parser.add_argument(
    "--no-parallel",
    dest='parallel',
    action='store_false',
    help="Do not run jobs in parallel")
# parser.add_argument(
    # "--create",
    # action='store_true',
    # help="Create packages after exporting them.")
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
  pc.baseline_config["package_defaults"]["version"] = "master"
  pc.baseline_config["package_defaults"]["channel"] = "devel"
  pc.baseline_config[prog_path.stem] = dict()
  pc.baseline_config[prog_path.stem]["packages_to_export"] = "all"
  pc.baseline_config[prog_path.stem]["scratch-folder"] = "_package-exports.d"
  if args.print_default_configuration:
    print("# Default Configuration")
    print(yaml.dump(pc.baseline_config))
    sys.exit(0)

  pc.load_configs(args.configuration)

  scratch_folder_path = Path(pc.config[prog_path.stem]["scratch-folder"])
  if scratch_folder_path.exists():
    shutil.rmtree(str(scratch_folder_path))
  scratch_folder_path.mkdir()

  pc.add_packages(package_paths)
  if args.print_configuration:
    print("# Complete Configuration")
    print(yaml.dump(pc.config))
    sys.exit(0)


  pc.export_environment()
  packages_to_export = pc.filter_packages( pc.config[prog_path.stem].get("packages_to_export","all") )
  with (Path(pc.config[prog_path.stem]["scratch-folder"]) / "conan_export.out" ).open('w') as f:
    print("Exporting packages: "+", ".join(packages_to_export))
    results = [ pc.export_package(package,f) for package in packages_to_export]
    print("Done")




