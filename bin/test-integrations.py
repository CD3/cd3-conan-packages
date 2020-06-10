#! /usr/bin/python3

import glob
import os
import pprint
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
    print("testing recipe in", conanfile)
    source_dir = Path(".")
    build_dir = source_dir / (package.name + ".build")
    outfile = Path(f"{package.name}.out")
    profile_opts = " ".join([f'-p "{p}"' for p in profiles])

    with open(outfile, "w") as f:

        print(util.INFO + f"Testing {package.name}" + util.EOL)
        print(
            util.INFO
            + f"""  Installing Dependencies with 'conan install "{conanfile}" {profile_opts} --build missing --install-folder="{build_dir}" """
            + util.EOL
        )
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

        print(
            util.INFO
            + f"""  Downloading Source with 'conan source "{conanfile}" --source-folder="{source_dir}" --install-folder="{build_dir}"' """
            + util.EOL
        )
        if (
            util.run(
                f'''conan source "{conanfile}" --source-folder="{source_dir}" --install-folder="{build_dir}"''',
                f,
                f,
            )
            != 0
        ):
            print(
                util.ERROR
                + f"There was an error downloading source for {package.name}. You can view the output in {str(outfile.resolve())}."
                + util.EOL
            )
            return 1

        print(
            util.INFO
            + f"""  Building with 'conan build "{conanfile}" --source-folder="{source_dir}" --install-folder="{build_dir}" --build-folder="{build_dir}"' """
            + util.EOL
        )
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
            print(util.INFO + "  Looking for unit tests to run." + util.EOL)

            # jump into the build directory
            with util.working_directory(build_dir):
                # search for unit tests
                for path in (
                    Path(dir)
                    for dir in ["testBin", package.name + "-testing"]
                    if Path(dir).is_dir()
                ):
                    for file in filter(
                        lambda p: p.is_file() and util.is_exe(p),
                        itertools.chain(
                            path.glob("*"), path.glob("Debug/*"), path.glob("Release/*")
                        ),
                    ):
                        print(
                            util.INFO
                            + "    Found "
                            + str(file)
                            + ". Running now."
                            + util.EOL
                        )
                        if util.run(f'''"{str(file.resolve())}"''', f, f) != 0:
                            print(
                                util.ERROR
                                + f"There was an error running unit tests. You can view the output in {str(outfile.resolve())}"
                                + util.EOL
                            )
                            return 1
        print(util.GOOD + "All Good!" + util.EOL)
        return 0


package_paths = [Path(file).parent for file in Path.cwd().glob("*/conanfile.py")]


@click.command()
@click.option(
    "--print-configuration",
    help="Print the configuration that will be used.",
    is_flag=True,
)
@click.option(
    "-t",
    "--tests",
    help="Comma-seprated list of packages to test. This will override any packages specified in the configuration file.",
)
@click.option(
    "-p", "--profile", help="Conan profile(s) to use for testing.", multiple=True
)
@click.option(
    "--unit-tests/--no-unit-tests", help="Run unit tests for a package during testing."
)
@click.option(
    "--skip-export/--no-skip-export",
    help="Skip exporting all recipes to local cache before testing.",
    default=False,
)
@click.option(
    "--clear-cache/--no-clear-cache",
    help="Clear local cache before exporting recipies.",
    default=True,
)
@click.option("-o","--owner",                  help ="Set owner to to use for package export.")
@click.option("-c","--channel",                help ="Set channel to to use for package export.")
@click.argument("config_file", type=click.Path(exists=True),required=False)
def main(
    print_configuration,
    tests,
    profile,
    unit_tests,
    skip_export,
    clear_cache,
    owner,
    channel,
    config_file,
):
    """
    Test conan-based build of packages.

    This script will export each of the packages in the repository to the local cache and then attempt to build them and run their unit tests.
    This is useful for testing that the latest commits on a given component did not break any of the components that depend on it. For example,
    if libA is updated, this script will run an verify that all of the packages dependeing on libA can still build and pass their unit tests.

    To do this, every package that gets exported by this script starts with a
    base recipe. You can then specify settings to override (see Configuration
    Settings below) to create a new recipe instance. If no override settings are
    specified, then the recipe instance will just be the base recipe.

        base recipe -> [override settigns] -> recipe instance

    Configuration:

    The exported packages can be configured using a YAML file and passing it as an argument to this script.

    Configuration Settings:

    \b
    global
        a namespace for global package settings (setting that will be applied to all packages)
    global.export
        a namespace for setting related to exporting packages.
    global.export.owner
        the default package owner for every exported package.
    global.export.channel
        the default package channel for every exported packages.
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
    test-integrations
        a namespace used for setting for this script
    test-integrations.scratch-folder
        the name of the directory used for writing data to disk (logs, temp files, etc)
    test-integrations.packages_to_test
        a list of packages to test. by default, all 'marked' packages  will be tested.
        to mark a package, place an empty file named 'test-integrations' in the package
        recipe folder next to the conanfile.py.
        

    Example Configuration Files:

    To test all package recipes in their current state:
    \b
    test-integrations:
      packages_to_test: all
      scratch-folder: _test-integrations.d
    global:
      export:
        channel: devel
        owner: MyOrg

    This will export all packages in the repository and then try to build and test each package
    that is marked with a test-integrations file.

    To test the latest commits on master for all packages.
    \b
    test-integrations:
      packages_to_test: all
      scratch-folder: _test-integrations.d
    
    global:
      setting_overrides:
        version: latest
        checkout: master
      export:
        channel: devel
        owner: MyOrg
      dependency_overrides:
        - '*/*@MyOrg/devel -> [name]/latest@MyOrg/devel'

    This will export all packages in the repository using the latest commit on master with the version
    set to 'latest'. Since the package recipes (probably) won't refer to the 'latest' version,
    We specify a dependency override that will replace all dependencies from the MyOrg/devel
    owner/channel with a reference to the latest version.
    """

    config = util.load_config( str(prog_path.parent / f"{prog_path.stem}-default-config.yaml" ), config_file) 

    if owner:
      config['global']['export']['owner'] = owner
    if channel:
      config['global']['export']['channel'] = channel

    # collect all packages to export.
    for file in Path("recipes").glob("*/conanfile.py"):
      config['package_instances'].append( {'conanfile':str(file.absolute()), 'name' : str(file.parent.stem) } )
    for file in Path("recipes").glob("*/conanfile-latest.py"):
      config['package_instances'].append( {'conanfile':str(file.absolute()), 'name' : str(file.parent.stem) } )

    # make sure all conanfiles are specified with absolute path
    for instance in config["package_instances"]:
      instance["conanfile"] = str(Path(instance["conanfile"]).absolute())


    if tests:
      if tests in ['all']:
        config[prog_path.stem]['packages_to_test'] = tests
      else:
        config[prog_path.stem]['packages_to_test'] = tests.split(",")

    if config[prog_path.stem].get('packages_to_test','all') == 'all':
      packages = list()
      for marker in Path("recipes").glob("*/test-integrations"):
        packages.append( marker.parent.stem )

      config[prog_path.stem]['packages_to_test'] = packages



    if print_configuration:
        print("# Complete Configuration")
        print(yaml.dump(config))
        sys.exit(0)

    pc = util.PackageCollection()
    pc.load(config)


    scratch_folder_path = Path(pc.config[prog_path.stem]["scratch-folder"])
    if not scratch_folder_path.exists():
      scratch_folder_path.mkdir()

    scratch_build_folder_path = scratch_folder_path/"builds"
    util.remove_path(scratch_build_folder_path)
    scratch_build_folder_path.mkdir()

    conan_cache_path = scratch_folder_path.absolute()/"conan_cache"
    # set teh CONAN_USER_HOME environment variable to a local directory so we don't
    # interfere with the global cache
    os.environ["CONAN_USER_HOME"] = str(conan_cache_path)
    if skip_export:
        print( "Skipping export step. Packages currently in the local cache will be tested.")
    else:
        if clear_cache:
            print(f"Removing conan cache (removing directory {str(conan_cache_path/'data')}).")
            util.remove_path(conan_cache_path/"data")
        print("Exporting packages")
        pc.export_packages()
        with (Path(pc.config[prog_path.stem]["scratch-folder"]) / "conan_export.out" ).open('w') as f:
          pc.export_packages( stdout = f)
        print("Done")


    packages_to_test = util.filter_packages( config[prog_path.stem]['packages_to_test'], pc.package_instances)

    print(
        util.EMPH
        + "Testing packages: "
        + ", ".join([p.name for p in packages_to_test])
        + util.EOL
    )
    with util.working_directory(scratch_build_folder_path):
        results = [
            test_package(package, profile, unit_tests) for package in packages_to_test
        ]
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
