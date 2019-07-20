#! /usr/bin/python3

import glob
import os
import stat
import subprocess
import multiprocessing
import shutil
import sys
import yaml
import itertools
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
parser.add_argument(
    "--unit-tests", dest="do_unit_tests", action="store_true", help="Attempt to run the unit tests for all packages being tested after they are built."
)
parser.add_argument(
    "--no-unit-tests",
    dest="do_unit_tests",
    action="store_false",
    help="Do not run unit tests during package testing.",
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
    help="Packages to test. This will override any packages specified in the configuration file.",
)
parser.add_argument(
    "--profile","-p",
    action="append",
    default=[],
    help="Conan profile",
)
parser.add_argument(
    "--skip-export",
    action="store_true",
    help="Skip exporting packages and just run tests.",
)

parser.add_argument(
    "--clear-cache",
    dest="clear_cache",
    action="store_true",
    default=True,
    help="Clear the cache before exporting packages.",
)

parser.add_argument(
    "--no-clear-cache",
    dest="clear_cache",
    action="store_false",
    default=True,
    help="Do not clear the cache before exporting packages.",
)

parser.set_defaults(parallel=True)
parser.set_defaults(do_unit_tests=True)
args = parser.parse_args()

prog_path = Path(parser.prog)


def test_package(package, do_unit_tests=True):
    conanfile = package.instance_conanfile
    source_dir = Path(".")
    build_dir = source_dir / (package.name + ".build")
    outfile = Path(f"{package.name}.out")
    profile_opts = " ".join([ f'-p "{p}"' for p in args.profile])

    with open(outfile, "w") as f:

        print(util.INFO+f"Testing {package.name}"+util.EOL)
        print(util.INFO+f'''  Installing Dependencies with 'conan install "{conanfile}" {profile_opts} --build missing --install-folder="{build_dir}" '''+util.EOL)
        if (
            util.run(
                f'''conan install "{conanfile}" {profile_opts} --build missing --install-folder="{build_dir}"''',
                f,
                f,
            )
            != 0
        ):
            print(
                util.ERROR
                + f"There was an error installing dependencies for {package.name}. You can view the output in {str(outfile.resolve())}."
                + util.EOL
            )
            f.write("\n\n")
            return 1

        print(util.INFO+f'''  Downloading Source with 'conan source "{conanfile}" --source-folder="{source_dir}" --install-folder="{build_dir}"' '''+util.EOL)
        if (
            util.run(f'''conan source "{conanfile}" --source-folder="{source_dir}" --install-folder="{build_dir}"''', f, f)
            != 0
        ):
            print(
                util.ERROR
                + f"There was an error downloading source for {package.name}. You can view the output in {str(outfile.resolve())}."
                + util.EOL
            )
            return 1

        print(util.INFO+f'''  Building with 'conan build "{conanfile}" --source-folder="{source_dir}" --install-folder="{build_dir}" --build-folder="{build_dir}"' '''+util.EOL)
        if (
            util.run(
                f'''conan build "{conanfile}" --source-folder="{source_dir}" --install-folder="{build_dir}" --build-folder="{build_dir}"''',
                f,
                f,
            )
            != 0
        ):
            print(
                util.ERROR
                + f"There was an error building {package.name}. You can view the output in {str(outfile.resolve())}."
                + util.EOL
            )
            return 1

        if do_unit_tests:
          print(util.INFO + "  Looking for unit tests to run."+util.EOL)

          # jump into the build directory
          with util.working_directory(build_dir):
              # search for unit tests
              for path in (
                  Path(dir)
                  for dir in ["testBin", package.name + "-testing"]
                  if Path(dir).is_dir()
              ):
                  for file in filter(
                      lambda p: p.is_file() and util.is_exe(p), itertools.chain( path.glob("*"),path.glob("Debug/*"),path.glob("Release/*") )
                  ):
                      print(util.INFO + "    Found " + str(file) + ". Running now."+util.EOL)
                      if util.run(f'''"{str(file.resolve())}"''', f, f) != 0:
                          print(
                              util.ERROR
                              + f"There was an error running unit tests. You can view the output in {str(outfile.resolve())}"
                              + util.EOL
                          )
                          return 1
        print( util.GOOD + "All Good!" + util.EOL)
        return 0


package_paths = [Path(file).parent for file in Path.cwd().glob("*/conanfile.py")]
if __name__ == "__main__":

    pc = util.PackageCollection()
    default_configuration_text = f'''
  package_defaults:
    version: testing
    channel: integration-tests
    owner: cd3
    git_url_basename: git@github.com:CD3
    checkout: master
  package_overrides:
    UnitTestCpp :
      version: "2.0"
      checkout: "v2.0.0"
      git_url_basename: "git://github.com/unittest-cpp"
    XercesC:
      version: "3.2.2"
      git_url_basename : null
      checkout : null
  {prog_path.stem}:
    packages_to_test:
      include: '.*'
      exclude:
       - UnitTestCpp
       - XercesC
    scratch-folder : "_{prog_path.stem}.d"
  '''
    pc.load( yaml.load( default_configuration_text, Loader=yaml.SafeLoader ) )
    if args.print_default_configuration:
      print("# Default Configuration")
      print(yaml.dump(pc.config))
      sys.exit(0)

    for file in args.configuration:
      pc.update( yaml.load( Path(file).read_text(), Loader=yaml.SafeLoader ) )

    pc.add_from_conan_recipe_collection(".")
    if args.print_configuration:
      print("# Complete Configuration")
      print(yaml.dump(pc.config))
      sys.exit(0)

    scratch_folder_path = Path(pc.config[prog_path.stem]["scratch-folder"])
    if scratch_folder_path.exists():
      # Can't remove directory on Windows unless all files are writeable.
      for root,dirs,files in os.walk(scratch_folder_path):
        for f in files:
          os.chmod(Path(root)/f, stat.S_IWRITE)
      shutil.rmtree(scratch_folder_path)
    scratch_folder_path.mkdir()


    
    if args.skip_export:
      print("Skipping export step. Packages currently in the local cache will be tested.")
    else:
      if args.clear_cache:
          print("Removing all packages in the 'integration-tests' channel.")
          util.run("conan remove -f */integration-tests")
      print("Exporting packages")
      with (scratch_folder_path / "conan_export.out" ).open('w') as f:
        pc.export_packages( config=pc.config[prog_path.stem].get("packages_to_export", "all"), stdout = f)
      print("Done")



    if args.test:
      packages_to_test = util.filter_packages( {'include' : args.test }, pc.packages )
    else:
      packages_to_test = util.filter_packages( pc.config[prog_path.stem].get('packages_to_test','all'), pc.packages )

    print(util.EMPH+"Testing packages: " + ", ".join([p.name for p in packages_to_test])+util.EOL)
    with util.working_directory(scratch_folder_path):
      results = [test_package(package, args.do_unit_tests) for package in packages_to_test]
    print("Done")

    num_tests = len(results)
    num_failed = sum(results)

    print("\n")
    print("Tested " + str(num_tests) + " Packages")
    if num_failed > 0:
        print(str(num_failed) + " Failed")
    else:
        print("All Tests Passed")
