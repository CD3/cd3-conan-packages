from conans import ConanFile, CMake, tools
import os
import platform
import pathlib
import glob
import io
import re

class ConanPackage(ConanFile):
    name = "libField"
    url = "https://github.com/CD3/cd3-conan-packages"

    author = "CD Clark III clifton.clark@gmail.com"
    description = "A C++ library for storing and working with field data."
    license = "MIT"
    topics = ("C++", "Physics")

    generators = "cmake", "virtualenv"
    requires = 'boost/1.72.0', 'hdf5/1.10.5@cd3/devel', 'zlib/1.2.11'

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    def build_requirements(self):
      self.tool_requires(f"cmake/[>3.16.0]")

    def source(self):
       tools.get(**self.conan_data["sources"][self.version], strip_root=True, destination=self._source_subfolder)

    def package(self):
        self.copy(pattern="LICENSE.md", dst="licenses", src=self._source_subfolder)
        # we are going to use cmake to package, even though this is header-only,
        # because there are some generated files that need to be included.

        # remove the `find_package(...)` calls from the CMakeLists.txt
        # so that we can just install files into package directory
        cmake_lists = pathlib.Path(self._source_subfolder)/"CMakeLists.txt"
        cmake_lists_content = cmake_lists.read_text()
        cmake_lists_content = re.sub(r"^\s*find_package\(.*$","",cmake_lists_content,flags=re.MULTILINE)
        cmake_lists_content = re.sub(r"^\s*add_subdirectory\(.*$","",cmake_lists_content,flags=re.MULTILINE)

        cmake_lists.write_text(cmake_lists_content)

        cmake = CMake(self)
        cmake.definitions["BUILD_TESTS"] = "OFF"
        cmake.configure(source_folder=self._source_subfolder)
        cmake.build()
        cmake.install()
        
    def package_id(self):
        self.info.header_only()

    def package_info(self):
        self.env_info.libField_DIR = os.path.join(self.package_folder, "cmake")

