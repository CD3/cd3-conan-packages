from conans import ConanFile, CMake, tools, errors
from conan.tools.cmake import CMakeDeps
import os
import platform
import pathlib
import glob
import io
import re

class ConanPackage(ConanFile):
    name = "libInterpolate"
    author = "CD Clark III clifton.clark@gmail.com"
    description = "A C++ library for numerical interpolation supporting multiple methods/algorithms."
    license = "MIT"
    topics = ("c++", "interpolation", "numerical interpolation")
    url = "https://github.com/CD3/cd3-conan-packages"
    

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    def build_requirements(self):
      self.tool_requires(f"cmake/[>3.16.0]")

    def source(self):
       tools.get(**self.conan_data["sources"][self.version], strip_root=True, destination=self._source_subfolder)

    def requirements(self):
        for req in self.conan_data["requirements"][self.version]:
            self.requires(req)


    def package(self):
        self.copy(pattern="LICENSE.md", dst="licenses", src=self._source_subfolder)

        # we are going to use cmake to package, even though this is header-only,
        # because there are some generated files that need to be included.

        # remove the `find_package(...)` calls from the CMakeLists.txt
        # so that we can just install files into package directory
        cmake_lists = pathlib.Path(self._source_subfolder)/"CMakeLists.txt"
        cmake_lists_content = cmake_lists.read_text()
        cmake_lists_content = re.sub(r"^\s*find_package\(.*$","",cmake_lists_content,flags=re.MULTILINE)
        if self.version == "2.6":
            cmake_lists_content = re.sub(r"^\s*add_subdirectory\(.*testing.*$","",cmake_lists_content,flags=re.MULTILINE)

        cmake_lists.write_text(cmake_lists_content)

        cmake = CMake(self)
        cmake.definitions["BUILD_TESTS"] = "OFF"
        cmake.configure(source_folder=self._source_subfolder)
        cmake.build()
        cmake.install()


    def package_id(self):
        self.info.header_only()

    def package_info(self):
        # a work-around to allow the cmake find package generator to use libInterpolate::Interpolate for the target name
        deps = []
        for req in self.conan_data["requirements"][self.version]:
            name = req.split('/')[0]
            deps.append(f'{name}::{name}')
        self.cpp_info.components["Interpolate"].requires = deps

        # allow virtualenv generator to find libInterpolateConfig.cmake
        self.env_info.libInterpolate_DIR = str(pathlib.Path(self.package_folder)/ "cmake")
