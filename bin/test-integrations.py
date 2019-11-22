#! /usr/bin/python3

"""
Test conan-based build of packages.

This script will export each of the packages in the repository to the local cache and then attempt to them and run their unit tests.
This is useful for testing that the latest commits on a given component did not break any of the components that depend on it. For example,
if libField is updated, this script will run an verify that all of the packages dependeing on libMPE can still build and pass their unit tests.

Usage:
  test-integrations.py (-h|--help)
  test-integrations.py [--test <name>]... [--profile <name>]... [options] [<config_file>...]
  test-integrations.py [options] [<config_file>...]

Arguments:
  <config_file>                   File(s) containing configurations to test.

Options:
  -h,--help                       This help message
  --no-unit-tests                 Do not run unit tests during package testing.
  --print-default-configuration   Print the default configuration.
  --print-configuration           Print the configuration that will be used.
  -t <name>,--test <name>         List of packages to test. This will override any packages specified in the configuration file.
  -p <name>,--profile <name>      Conan profile to use for testing.
  --skip-export                   Skip exporting packages and just run tests.
  --no-clear-cache                Do not clear the cache before exporting packages.
"""

import docopt
args = docopt.docopt(__doc__, version='x.x')



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


prog_path = Path(sys.argv[0]).resolve()


def test_package(package, do_unit_tests=True):
    conanfile = package.instance_conanfile
    source_dir = Path(".")
    build_dir = source_dir / (package.name + ".build")
    outfile = Path(f"{package.name}.out")
    profile_opts = " ".join([ f'-p "{p}"' for p in args['--profile']])

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
    if args['--print-default-configuration']:
      print("# Default Configuration")
      print(yaml.dump(pc.config))
      sys.exit(0)

    for file in args['<config_file>']:
      pc.update( yaml.load( Path(file).read_text(), Loader=yaml.SafeLoader ) )

    pc.add_from_conan_recipe_collection(".")
    if args['--print-configuration']:
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


    
    if args['--skip-export']:
      print("Skipping export step. Packages currently in the local cache will be tested.")
    else:
      if not args['--no-clear-cache']:
          print("Removing all packages in the 'integration-tests' channel.")
          util.run("conan remove -f */integration-tests")
      print("Exporting packages")
      with (scratch_folder_path / "conan_export.out" ).open('w') as f:
        pc.export_packages( config=pc.config[prog_path.stem].get("packages_to_export", "all"), stdout = f)
      print("Done")



    if args['--test']:
      packages_to_test = util.filter_packages( {'include' : args['--test'] }, pc.packages )
    else:
      packages_to_test = util.filter_packages( pc.config[prog_path.stem].get('packages_to_test','all'), pc.packages )

    print(util.EMPH+"Testing packages: " + ", ".join([p.name for p in packages_to_test])+util.EOL)
    with util.working_directory(scratch_folder_path):
      results = [test_package(package, not args['--no-unit-tests']) for package in packages_to_test]
    print("Done")

    num_tests = len(results)
    num_failed = sum(results)

    print("\n")
    print("Tested " + str(num_tests) + " Packages")
    if num_failed > 0:
        print(str(num_failed) + " Failed")
    else:
        print("All Tests Passed")
