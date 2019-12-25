#! /usr/bin/python3

import glob
import os
import stat
import shutil
import sys
import yaml
import itertools
from pathlib import Path

import util

import click


prog_path = Path(sys.argv[0]).resolve()


def test_package(package, profiles, do_unit_tests=True):
    conanfile = package.instance_conanfile
    print("testing recipe in",conanfile)
    source_dir = Path(".")
    build_dir = source_dir / (package.name + ".build")
    outfile = Path(f"{package.name}.out")
    profile_opts = " ".join([ f'-p "{p}"' for p in profiles])

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
@click.command()
@click.option("--print-default-configuration",  help ="Print the default configuration.",is_flag=True)
@click.option("--print-configuration",          help ="Print the configuration that will be used.",is_flag=True)
@click.option("-t","--test",                    help ="List of packages to test. Thsi will override any packages specified in the configuration file.",multiple=True)
@click.option("-p","--profile",                 help ="Conan profile(s) to use for testing.",multiple=True)
@click.option("--unit-tests/--no-unit-tests",   help ="Run unit tests for a package during testing.")
@click.option("--skip-export/--no-skip-export", help ="Skip exporting all recipes to local cache before testing.",default=False)
@click.option("--clear-cache/--no-clear-cache", help ="Clear local cache before exporting recipies.",default=True)
@click.argument("config_file",nargs=-1)
def main(print_default_configuration,print_configuration,test,profile,unit_tests,skip_export,clear_cache,config_file):
    """
    Test conan-based build of packages.

    This script will export each of the packages in the repository to the local cache and then attempt to them and run their unit tests.
    This is useful for testing that the latest commits on a given component did not break any of the components that depend on it. For example,
    if libField is updated, this script will run an verify that all of the packages dependeing on libMPE can still build and pass their unit tests.
    """

    pc = util.PackageCollection()
    default_configuration_text = f'''
global:
  export:
    channel: integration-tests
    owner: none
  setting_overrides:
    checkout: master
    version: testing
  dependency_overrides: []
package_instances: []
{prog_path.stem}:
  scratch-folder : "_{prog_path.stem}.d"
  '''
    config = yaml.load( default_configuration_text, Loader=yaml.SafeLoader )
    if print_default_configuration:
      print("# Default Configuration")
      print(yaml.dump(config))
      sys.exit(0)

    for file in config_file:
      util.update_dict( config, yaml.load( Path(file).read_text(), Loader=yaml.SafeLoader ) )

    for marker in Path("recipes").glob("*/test-integrations"):
      file = marker.parent / "conanfile.py"
      if not file.exists():
        print(util.WARN + f"WARNING: did not find conanfile.py next to {str(marker)}. Skipping"+util.EOL)
      config['package_instances'].append( {'conanfile':str(file.absolute()), 'name' : str(file.parent.stem) } )
      config['global']['dependency_overrides'].append(f"{file.parent.stem}/testing@none/integration-tests")

    if print_configuration:
      print("# Complete Configuration")
      print(yaml.dump(config))
      sys.exit(0)

    pc.load(config)

    scratch_folder_path = Path(pc.config[prog_path.stem]["scratch-folder"])
    if scratch_folder_path.exists():
      # Can't remove directory on Windows unless all files are writeable.
      for root,dirs,files in os.walk(scratch_folder_path):
        for f in files:
          os.chmod(Path(root)/f, stat.S_IWRITE)
      shutil.rmtree(scratch_folder_path)
    scratch_folder_path.mkdir()


    
    if skip_export:
      print("Skipping export step. Packages currently in the local cache will be tested.")
    else:
      if clear_cache:
          print("Removing all packages in the 'integration-tests' channel.")
          util.run("conan remove -f */integration-tests")
      print("Exporting packages")
      with (scratch_folder_path / "conan_export.out" ).open('w') as f:
        pc.export_packages( config=pc.config[prog_path.stem].get("packages_to_export", "all"), stdout = f)
      print("Done")


    if test:
      packages_to_test = util.filter_packages( {'include' : list(test) }, pc.package_instances )
    else:
      packages_to_test = util.filter_packages( pc.config[prog_path.stem].get('packages_to_test','all'), pc.package_instances )

    print(util.EMPH+"Testing packages: " + ", ".join([p.name for p in packages_to_test])+util.EOL)
    with util.working_directory(scratch_folder_path):
      results = [test_package(package, profile, unit_tests) for package in packages_to_test]
    print("Done")

    num_tests = len(results)
    num_failed = sum(results)

    print("\n")
    print("Tested " + str(num_tests) + " Packages")
    if num_failed > 0:
        print(str(num_failed) + " Failed")
    else:
        print("All Tests Passed")

if __name__ == "__main__":
  main()
