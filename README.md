# Conan Package Recipes for CD3 Projects

This is a collection of recipes and utilities for building conan packages for various libraries I have written or use. Conan greatly simplifies
managing project dependencies, so it is easy to use a project that depends on another project. You just tell conan
what your project dependencies are, and it will automatically locate and configure them for you.

# Using

Note: several of these libraries are available at https://api.bintray.com/conan/cd3/conan-devel. This repo is used to develop those packages.
If you just want to use the libraries, add a remote to your conan.

```
$ conan remote add cd3 https://api.bintray.com/conan/cd3/conan-devel 
```

Package recipes are stored in the `recipes/` directory. Some projects have snapshots of recipes for older versions, with the latest recipe named `conanfile.py`.
Te export a recipe, you just need to run the `conan export` with the recipe file. For example:

```
$ conan export ./recipes/libField/conanfile.py
```

This will export the recipe without a user/channel. To add a `user/channel` string, just pass it as another argument:
```
$ conan export ./recipes/libField/conanfile.py cd3/devel
```

The `export-recipes.py` script will export all of the recipes in the repository with the user channel string `cd3/devel`

```
$ python export-recipes.py
```

Conan can download and build packages on demand, so no packages are built during the install. You will only download and build
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
libField/master@cd3/devel
```

`libField` depends on Boost, but you don't need to add boost as a requirement unless your project uses it directly. Conan will download
boost so that it can build `libField`. No you can use conan to install your dependencies, and build your dependencies.

```
$ mkdir build
$ cd build
$ conan install .. --build missing
```

The `--build missing` option tells conan to download the source code and build any project that are not in the local cache.
Since the `install.py` script does not build any packages, this will download and build `libField`. But this will only be done
once. If you require `libField` from another project, conan will use the package that it already build.

Running `conan install` will create a script named `activate.sh` (or `activate.bat` on Windows). This script contains
environment variable settings that tell CMake how to find the dependencies, so to build your project, just run:

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
    requires = 'libField/master@cd3/devel'

    def build(self):
      cmake = CMake(self)
      cmake.configure()
      cmake.build()
```

Now you can install your dependencies and build your project with two commands

'''
$ mkdir build
$ cd build
$ conan install .. --build missing
$ conan build ..
'''
