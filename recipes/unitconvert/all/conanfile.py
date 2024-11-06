import pathlib

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, replace_in_file


class ConanPackage(ConanFile):
    name = "unitconvert"

    author = "CD Clark III clifton.clark@gmail.com"
    description = "A C++ library for runtime unit conversions."
    license = "MIT"
    topics = ("C++", "physics", "dimensional analysis", "unit conversions")
    url = "https://github.com/CD3/cd3-conan-packages"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}

    requires = "boost/1.86.0"

    def config_options(self):
        if self.settings.os == "Windows":
            self.options.rm_safe("fPIC")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self)

    def generate(self):
        deps = CMakeDeps(self)
        deps.generate()
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_UNIT_TESTS"] = False
        tc.generate()

    def source(self):
        get(
            self,
            **self.conan_data["sources"][self.version],
            strip_root=True,
        )
        replace_in_file(
            self,
            "CMakeLists.txt",
            'set_target_properties( ${LIB_NAME} PROPERTIES DEBUG_POSTFIX "-d" )',
            "",
        )

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "UnitConvert")
        self.cpp_info.set_property("cmake_target_name", "UnitConvert::UnitConvert")
        self.cpp_info.libs = ["UnitConvert"]
