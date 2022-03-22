from conans import ConanFile, CMake, tools, errors
import os
import platform
import pathlib
import io
import re

class ConanPackage(ConanFile):
    name = "unitconvert"

    author = "CD Clark III clifton.clark@gmail.com"
    description = "A C++ library for runtime unit conversions."
    license = "MIT"
    topics = ("C++", "physics", "dimensional analysis", "unit conversions")
    url = "https://github.com/CD3/cd3-conan-packages"

    generators = "cmake", "virtualenv"
    requires = 'boost/1.72.0'
    settings = "os", "compiler", "build_type", "arch"

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    def build_requirements(self):
      self.tool_requires(f"cmake/[>3.16.0]")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version], strip_root=True, destination=self._source_subfolder)
        tools.replace_in_file( f"{self._source_subfolder}/CMakeLists.txt", 'set_target_properties( ${LIB_NAME} PROPERTIES DEBUG_POSTFIX "-d" )', "")


    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions['BUILD_UNIT_TESTS'] = False
        # if self.options["boost"].shared:
        #   cmake.definitions["Boost_USE_STATIC_LIBS"] = "OFF"
        # else:
        #   cmake.definitions["Boost_USE_STATIC_LIBS"] = "ON"

        cmake.configure(source_folder=self._source_subfolder)

        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        cmake = self._configure_cmake()
        cmake.install()
        
    def package_info(self):
        self.env_info.UnitConvert_DIR = os.path.join(self.package_folder, "cmake")
        self.cpp_info.names["cmake_find_package"] = "UnitConvert"
        self.cpp_info.names["cmake_find_package_multi"] = "UnitConvert"
        self.cpp_info.libs = ['UnitConvert']

