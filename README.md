# Conan Package Recipes for CD3 Projects

This is a collection of recipes and utilities for building conan packages for various libraries I have written or use. Conan greatly simplifies
managing project dependencies, so it is easy to use a project that depends on another project. You just tell conan
what your project dependencies are, and it will automatically locate and configure them for you.

# Using

Note: several of these libraries are available at https://cdc3.jfrog.io/artifactory/default-conan/. This repo is used to develop those packages.
If you just want to use the libraries, add a remote to your conan.

```
$ conan remote add cd3 https://cdc3.jfrog.io/artifactory/api/conan/default-conan
```

Note that my JFrog server name is `cdc3.jfrog.io`, not `cd3`. My original account got deleted for lack of traffic, but the old is unavailable now for some reason.

Package recipes are stored in the `recipes/` directory. Originally, I stored recipes for all versions, including the latest version, in the same directory, with
the latest version recipe named `conanfile.py`. Other version recipes were named `conanfile-x.x.x.py`. I have recently begun following the
[conan-center-index](https://github.com/conan-io/conan-center-index) convention
of storing recipes in subdirectories, and using `config.yml` files to specify
the version-to-file mapping. So, it is no longer possible to export these recipes by simply calling `conan export ...` with the recipe file name.
You will have to also specify the package name and version

```
$ conan export ./recipes/libField/all/conanfile.py libField/0.9@ # can't just do conan export ./recipes/libField/all/conanfile.py anymore...
```

Fortunately, the `export-recipes.py` script is provided to export all of the recipes in the repository automatically. By default, it will export
all recipes with the user channel string `cd3/devel`

```
$ python export-recipes.py
```

Conan can download and build packages on demand, so no packages are built when the `export-recipes.py` script is run. You will only download and build
packages that your project actually depends on.

To use a package in your project, use CMake's `find_package` command to find the package. Each package imports a target that you can link against. For example, to use `libField`:

```cmake
...
find_package( libField REQUIRED )
... define your target(s)
target_link_library( myTarget libField::Field )
```

So far, this doesn't require conan. You could build and install `libField` manually, and use this to link against it.
But conan can do this for you automatically. To use conan, create a `conanfile.txt` file that lists `libField` as a requirement.

```
[requires]
libField/0.9@cd3/devel
```

`libField` depends on Boost, but you don't need to add boost as a requirement unless your project uses it directly. Conan will download
boost so that it can build `libField`. Now you can use conan to install your dependencies, and build your dependencies.

```
$ mkdir build
$ cd build
$ conan install .. --build missing
```

The `--build missing` option tells conan to download the source code and build any project that are not in the local cache.
Since the `export-recipes.py` script does not _build_ any packages, this will download and build `libField`. But this will only be done
once. If you require `libField` from another project (with the same version and settings), conan will use the package that it already build.

Running `conan install` will create a script named `activate.sh` (or `activate.bat` on Windows). This script contains
environment variable settings that tell CMake how to find the dependencies, so to build your project, you can just run:

```
$ source activate.sh
$ cmake ..
$ cmake --build .
```

Conan can also build your project for you, using cmake. The advantage of doing this is that you do not need to run the activate script.
You just need to provide a `conanfile.py` script that contains a `build` method. A minimum example looks like this:

```
from conans import ConanFile, CMake

class ConanBuild(ConanFile):
    generators = "cmake", "virtualenv"
    requires = 'libField/0.9@cd3/devel'

    def build(self):
      cmake = CMake(self)
      cmake.configure()
      cmake.build()
```

Now you can install your dependencies and build your project with two commands

```
$ mkdir build
$ cd build
$ conan install .. --build missing
$ conan build ..
```
