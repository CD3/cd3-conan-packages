from conans import ConanFile, CMake, tools
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps
import os
import platform
import pathlib
import glob
import io
import re

class ConanPackage(ConanFile):
    name = "libGBP"
    url = "https://github.com/CD3/cd3-conan-packages"

    author = "CD Clark III clifton.clark@gmail.com"
    description = "A C++ library Gaussian bean propagation calculations."
    license = "MIT"
    topics = ("C++", "Physics")

    requires = 'boost/1.72.0', 'eigen/3.3.7', 'BoostUnitDefinitions/0.2@cd3/devel'
    settings = "os", "compiler", "build_type", "arch"

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])

    def package(self):

        self.copy('*.hpp', src=f'libGBP-{self.version}/src', dst='include')
        self.copy('LICENSE.md', src=f'libGBP-{self.version}')
        
    def package_id(self):
        self.info.header_only()

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name","libGBP")
        self.cpp_info.set_property("cmake_target_name","libGBP::GBP")

