from conans import ConanFile, CMake, tools
import os, glob, io, re, pathlib

class ConanPackage(ConanFile):
    name = "BoostUnitDefinitions"
    url = "https://github.com/CD3/cd3-conan-packages"

    settings = "os", "compiler", "build_type", "arch"
    requires = 'boost/1.72.0'

    author = "CD Clark III clifton.clark@gmail.com"
    description = "A set of unit definitions for doing physical calculations with Boost.Units."
    license = "MIT"
    topics = ("C++", "Physics")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])

    def package(self):

        self.copy('*.hpp', src=f'BoostUnitDefinitions-{self.version}/src', dst='include')
        self.copy('LICENSE.md', src=f'BoostUnitDefinitions-{self.version}')

    def package_id(self):
        self.info.header_only()

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name","BoostUnitDefinitions")
        self.cpp_info.set_property("cmake_target_name","BoostUnitDefinitions::BoostUnitDefinitions")

