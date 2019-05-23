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

parser = ArgumentParser(description="Test conan-based build of packages.")
parser.add_argument(
    "configuration",
    action="store",
    nargs="*",
    help="File(s) contianing configurations to test.",
)
# parser.add_argument(
    # "--parallel", dest="parallel", action="store_true", help="Run jobs in parallel"
# )
# parser.add_argument(
    # "--no-parallel",
    # dest="parallel",
    # action="store_false",
    # help="Do not run jobs in parallel",
# )
parser.add_argument(
    "--unit-tests", dest="do_unit_tests", action="store_true", help="Attempt to run the unit tests for all packages being tested after they are built."
)
parser.add_argument(
    "--no-unit-tests",
    dest="do_unit_tests",
    action="store_false",
    help="Do not run unit tests during package testing. Only build.",
)
parser.add_argument(
    "--print-default-configuration",
    action="store_true",
    help="Print the default configuration.",
)
parser.add_argument(
    "--print-configuration",
    action="store_true",
    help="Print the configuration that will be used..",
)
parser.add_argument(
    "--test", "-t",
    action="append",
    help="Packages to tests. This will override any packages specified in the configuration file.",
)
parser.add_argument(
    "--profile",
    action="store",
    default="default",
    help="Conan profile",
)
parser.set_defaults(parallel=True)
parser.set_defaults(do_unit_tests=True)
args = parser.parse_args()

prog_path = Path(parser.prog)


def test_package(scratch_folder_path, package_name, do_unit_tests=True):
    pdir = Path(package_name)
    conanfile = pdir / "conanfile-static.py"
    if not conanfile.is_file():
        conanfile = pdir / "conanfile.py"
    source_dir = scratch_folder_path
    build_dir = source_dir / pdir / "build"
    outfile = scratch_folder_path / f"{package_name}.out"

    with open(outfile, "w") as f:

        print(package_name + ":Downloading Source with 'conan source ...'")
        if (
            util.run(f"conan source {conanfile} --source-folder={source_dir}", f, f)
            != 0
        ):
            print(
                util.ERROR
                + f"There was an error downloading source for {package_name}. You can view the output in {outfile}."
                + util.EOL
            )
            return 1

        print(package_name + ":Installing Dependencies with 'conan install ...'")
        if (
            util.run(
                f"conan install {conanfile} --profile {args.profile} --build missing --install-folder={build_dir}",
                f,
                f,
            )
            != 0
        ):
            print(
                util.ERROR
                + f"There was an error installing dependencies for {package_name}. You can view the output in {outfile}."
                + util.EOL
            )
            f.write("\n\n")
            return 1

        print(package_name + ":Building with 'conan build ...'")
        if (
            util.run(
                f"conan build {conanfile} --source-folder={source_dir} --install-folder={build_dir} --build-folder={build_dir}",
                f,
                f,
            )
            != 0
        ):
            print(
                util.ERROR
                + f"There was an error building {package_name}. You can view the output in {outfile}."
                + util.EOL
            )
            return 1

        if do_unit_tests:
          print(package_name + ":Looking for unit tests to run.")

          # jump into the build directory
          with util.working_directory(build_dir):
              # search for unit tests
              for path in (
                  Path(dir)
                  for dir in ["testBin", package_name + "-testing"]
                  if Path(dir).is_dir()
              ):
                  for file in filter(
                      lambda p: p.is_file() and os.access(str(p), os.X_OK), path.glob("*")
                  ):
                      print("  Found " + str(file) + ". Running now.")
                      if util.run(str(file.resolve()), f, f) != 0:
                          print(
                              util.ERROR
                              + f"There was an error running unit tests. You can view the output in {outfile}"
                              + util.EOL
                          )
                          return 1
        return 0


package_paths = [Path(file).parent for file in Path.cwd().glob("*/conanfile.py")]
if __name__ == "__main__":

    pc = util.PackageCollection()

    pc.baseline_config["package_defaults"]["version"] = "testing"
    pc.baseline_config["package_defaults"]["channel"] = "integration-tests"
    pc.baseline_config[prog_path.stem] = dict()
    pc.baseline_config[prog_path.stem]["packages_to_test"] = "all"
    pc.baseline_config[prog_path.stem]["packages_to_export"] = "all"
    pc.baseline_config[prog_path.stem]["scratch-folder"] = "_test-integrations-{}.d"
    if args.print_default_configuration:
        print("# Default Configuration")
        print(yaml.dump(pc.baseline_config))
        sys.exit(0)

    pc.load_configs(args.configuration)

    scratch_folder_path = Path(pc.config[prog_path.stem]["scratch-folder"].format(args.profile))
    if scratch_folder_path.exists():
        shutil.rmtree(str(scratch_folder_path))
    scratch_folder_path.mkdir()

    pc.add_packages(package_paths)
    if args.print_configuration:
        print("# Complete Configuration")
        print(yaml.dump(pc.config))
        sys.exit(0)

    packages_to_export = pc.filter_packages(
        pc.config[prog_path.stem].get("packages_to_export", "all")
    )
    with (scratch_folder_path / "conan_export.out").open(
        "w"
    ) as f:
        print("Exporting packages: " + ", ".join(packages_to_export))
        results = [pc.export_package(package, f) for package in packages_to_export]
        print("Done")

    if args.test:
      packages_to_test = args.test
    else:
      packages_to_test = pc.filter_packages(
          pc.config[prog_path.stem].get("packages_to_test", "all")
      )
    print("Testing packages: " + ", ".join(packages_to_test))
    results = [test_package(scratch_folder_path, package, args.do_unit_tests) for package in packages_to_test]
    print("Done")

    num_tests = len(results)
    num_failed = sum(results)

    print("\n")
    print("Tested " + str(num_tests) + " Packages")
    if num_failed > 0:
        print(str(num_failed) + " Failed")
    else:
        print("All Tests Passed")
