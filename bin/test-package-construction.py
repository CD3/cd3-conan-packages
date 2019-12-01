import pathlib
import subprocess

import click

@click.command()
@click.option("-s","--source",  help="Run the 'conan source' step.",is_flag=True)
@click.option("-i","--install", help="Run the 'conan install' step.",is_flag=True)
@click.option("-b","--build",   help="Run the 'conan build' step.",is_flag=True)
@click.option("-p","--package", help="Run the 'conan package' step.",is_flag=True)
@click.argument("conanfile_file_or_dir",type=click.Path())
def main(source,install,build,package,conanfile_file_or_dir):
  """
  Run steps to create a for a conan package locally.

  This script just automates running the conan commands to build and package
  a recipe individually during testing. If you wanted to do this manually, you
  would have to do something like

  \b
  ```
  $ conan source --source-folder=/path/to/source-dir /path/to/conanfile.py
  $ conan install --install-folder=/path/to/build-dir /path/to/conanfile.py
  $ conan build --source-folder=/path/to/source-dir --build-folder=/path/to/build-dir /path/to/conanfile.py
  $ conan package --source-folder=/path/to/source-dir --build-folder=/path/to/build-dir --package-folder=/path/to/package-dir /path/to/conanfile.py
  ```

  This script simply runs these commands with default paths

  \b
  /path/to/source-dir:   ./_tmp/<package_name>.source.d
  /path/to/build-dir:    ./_tmp/<package_name>.build.d
  /path/to/package-dir:  ./_tmp/<package_name>.package.d
  """


  conanfile = pathlib.Path(conanfile_file_or_dir)
  if conanfile.is_dir():
    conanfile = conanfile / "conanfile.py"

  package_name = str(conanfile.parent.stem)

  tmp_dir = pathlib.Path("_tmp")
  source_dir=tmp_dir/f"{package_name}-source.d"
  build_dir=tmp_dir/f"{package_name}-build.d"
  package_dir=tmp_dir/f"{package_name}-package.d"

  if not tmp_dir.exists():
    tmp_dir.mkdir()

  if source:
    cmd = ["conan", "source", "--source-folder", f"{str(source_dir)}", f"{str(conanfile)}"]
    subprocess.run(cmd)
  if install:
    cmd = ["conan", "install", "--install-folder", f"{str(build_dir)}", "--build", "missing", f"{str(conanfile)}"]
    subprocess.run(cmd)
  if build:
    cmd = ["conan", "build", "--source-folder", f"{str(source_dir)}", "--build-folder", f"{str(build_dir)}", f"{str(conanfile)}"]
    subprocess.run(cmd)
  if package:
    cmd = ["conan", "package", "--source-folder", f"{str(source_dir)}", "--build-folder", f"{str(build_dir)}", "--package-folder", f"{str(package_dir)}", f"{str(conanfile)}"]
    subprocess.run(cmd)


if __name__ == "__main__":
  main()
