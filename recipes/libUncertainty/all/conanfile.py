from conans import ConanFile, CMake, tools, errors
from conan.tools.cmake import CMakeDeps
import os
import platform
import pathlib
import glob
import io
import re

class ConanPackage(ConanFile):
    name = "libUncertainty"
    author = "CD Clark III clifton.clark@gmail.com"
    description = "A C++ library for working with uncertain quantities."
    license = "MIT"
    topics = ("c++", "error propagation", "uncertainty")
    url = "https://github.com/CD3/cd3-conan-packages"
    

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    def build_requirements(self):
      self.tool_requires(f"cmake/[>3.16.0]")

    def source(self):
       tools.get(**self.conan_data["sources"][self.version], strip_root=True, destination=self._source_subfolder)

    def requirements(self):
        if "requirements" in self.conan_data:
            for req in self.conan_data["requirements"][self.version]:
                self.requires(req)


    def package(self):
        self.copy(pattern="LICENSE.md", dst="licenses", src=self._source_subfolder)

        # we are going to use cmake to package, even though this is header-only,
        # because there are some generated files that need to be included.
        cmake = CMake(self)
        cmake.definitions["BUILD_UNIT_TESTS"] = "OFF"
        cmake.configure(source_folder=self._source_subfolder)
        cmake.build()
        cmake.install()


    def package_id(self):
        self.info.header_only()

    def package_info(self):
        # allow virtualenv generator to find libInterpolateConfig.cmake
        self.env_info.libInterpolate_DIR = str(pathlib.Path(self.package_folder)/ "cmake")
