from conans import ConanFile, CMake, tools, errors
from conan.tools.cmake import CMakeDeps
import os
import platform
import pathlib
import glob
import io
import re

class ConanPackage(ConanFile):
    name = "libuncertainty"
    author = "CD Clark III clifton.clark@gmail.com"
    description = "A C++ library for tracking uncertainty and error propgation."
    license = "MIT"
    topics = ("c++", "uncertainty", "error propagation")
    url = "https://github.com/CD3/cd3-conan-packages"
    

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    def build_requirements(self):
      self.tool_requires(f"cmake/[>3.16.0]")

    def source(self):
       tools.get(**self.conan_data["sources"][self.version], strip_root=True, destination=self._source_subfolder)

    def package(self):
        self.copy(pattern="LICENSE.md", dst="licenses", src=self._source_subfolder)

        cmake = CMake(self)
        cmake.definitions["BUILD_UNIT_TESTS"] = "OFF"
        # the libUncertainty CMakeLists.txt does not handle generating the version.h file
        # correctly when build outside of a git repository. we need to pass the version information
        # in
        cmake.definitions["GIT_COMMIT_DESC"] = f"{self.version}"
        cmake.definitions["GIT_COMMIT_BRANCH"] = f"conan"
        cmake.configure(source_folder=self._source_subfolder)
        cmake.build()
        cmake.install()


    def package_id(self):
        self.info.header_only()

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "libUncertainty"
        self.cpp_info.names["cmake_find_package_multi"] = "libUncertainty"
        # allow virtualenv generator to find libUncertaintyConfig.cmake
        self.env_info.libUncertainty_DIR = str(pathlib.Path(self.package_folder)/ "cmake")
