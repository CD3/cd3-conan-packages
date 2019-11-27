"""
Run steps to create a for a conan package locally.

This script just automates running the conan commands to build and package
a recipe individually during testing. If you wanted to do this manually, you
would have to do something like

```
$ conan source --source-folder=/path/to/source-dir /path/to/conanfile.py
$ conan install --install-folder=/path/to/build-dir /path/to/conanfile.py
$ conan build --source-folder=/path/to/source-dir --build-folder=/path/to/build-dir /path/to/conanfile.py
$ conan package --source-folder=/path/to/source-dir --build-folder=/path/to/build-dir --package-folder=/path/to/package-dir /path/to/conanfile.py
```

This script simply runs these commands with default paths

/path/to/source-dir:   ./_tmp/<package_name>.source.d
/path/to/build-dir:    ./_tmp/<package_name>.build.d
/path/to/package-dir:  ./_tmp/<package_name>.package.d

Usage:
  run-conan-create-steps.py (-h|--help)
  run-conan-create-steps.py [options] <conanfile_file_or_dir>

Options:
  -h,--help         This help message
  -s,--source       Run the 'conan source' step.
  -i,--install      Run the 'conan install' step.
  -b,--build        Run the 'conan build' step.
  -p,--package      Run the 'conan build' step.
"""

import docopt
args = docopt.docopt(__doc__, version='0.1')

import pathlib
import subprocess

conanfile = pathlib.Path(args['<conanfile_file_or_dir>'])
if conanfile.is_dir():
  conanfile = conanfile / "conanfile.py"

package_name = str(conanfile.parent.stem)

tmp_dir = pathlib.Path("_tmp")
source_dir=tmp_dir/f"{package_name}-source.d"
build_dir=tmp_dir/f"{package_name}-build.d"
package_dir=tmp_dir/f"{package_name}-package.d"

if not tmp_dir.exists():
  tmp_dir.mkdir()

if args['--source']:
  cmd = ["conan", "source", "--source-folder", f"{str(source_dir)}", f"{str(conanfile)}"]
  subprocess.run(cmd)
if args['--install']:
  cmd = ["conan", "install", "--install-folder", f"{str(build_dir)}", "--build", "missing", f"{str(conanfile)}"]
  subprocess.run(cmd)
if args['--build']:
  cmd = ["conan", "build", "--source-folder", f"{str(source_dir)}", "--build-folder", f"{str(build_dir)}", f"{str(conanfile)}"]
  subprocess.run(cmd)
if args['--package']:
  cmd = ["conan", "package", "--source-folder", f"{str(source_dir)}", "--build-folder", f"{str(build_dir)}", "--package-folder", f"{str(package_dir)}", f"{str(conanfile)}"]
  subprocess.run(cmd)


