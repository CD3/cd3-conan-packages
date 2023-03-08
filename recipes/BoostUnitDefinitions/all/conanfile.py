from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain
from conan.tools.files import get,copy
import os, glob, io, re, pathlib

class ConanPackage(ConanFile):
    name = "boost-unit-definitions"
    url = "https://github.com/CD3/cd3-conan-packages"

    settings = "os", "compiler", "build_type", "arch"
    requires = 'boost/1.72.0'

    author = "CD Clark III clifton.clark@gmail.com"
    description = "A set of unit definitions for doing physical calculations with Boost.Units."
    license = "MIT"
    topics = ("C++", "Physics")

    def source(self):
        get(self,**self.conan_data["sources"][self.version])

    def package(self):
        copy(self,'*.hpp', f'BoostUnitDefinitions-{self.version}/src', os.path.join(self.package_folder,'include'))
        copy(self,'LICENSE.md', f'BoostUnitDefinitions-{self.version}', self.package_folder)

    def package_id(self):
        self.info.clear()

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name","BoostUnitDefinitions")
        self.cpp_info.set_property("cmake_target_name","BoostUnitDefinitions::BoostUnitDefinitions")

