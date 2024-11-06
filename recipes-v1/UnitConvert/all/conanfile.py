from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps
from conan.tools.files import get, copy, replace_in_file, rmdir
from conan.tools.layout import cmake_layout
from conan.tools.scm import Version
import os
import pathlib


required_conan_version = ">=1.52.0"


class PackageConan(ConanFile):
    name = "UnitConvert"
    description = "A C++ library for runtime unit conversions."
    license = "MIT"
    url = "https://github.com/CD3/cd3-conan-packages"
    homepage = "https://github.com/CD3/UnitConvert"
    topics = ("physical dimensions")
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    @property
    def _min_cppstd(self):
        return 14

    @property
    def _compilers_minimum_version(self):
        return {
            "Visual Studio": "15",
            "msvc": "19.0",
            "gcc": "5",
            "clang": "5",
            "apple-clang": "5.1",
        }

    def export_sources(self):
        pass

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires("boost/1.80.0", transitive_headers=True)

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, self._min_cppstd)
        minimum_version = self._compilers_minimum_version.get(
            str(self.settings.compiler), False
        )
        if (
            minimum_version
            and Version(self.settings.compiler.version) < minimum_version
        ):
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, f"CMakeLists.txt", "GIT_VERSION(UnitConvert)", f"set(UnitConvert_VERSION {self.version})")
        replace_in_file(self, f"CMakeLists.txt", "add_subdirectory( testing )", f"")
        replace_in_file(self, f"CMakeLists.txt", 'set_target_properties( ${LIB_NAME} PROPERTIES DEBUG_POSTFIX "-d" )', f"")
        

    def generate(self):
        gen = CMakeToolchain(self)
        gen.variables["BUILD_UNIT_TESTS"] = False
        # gen.variables["UnitConvert_VERSION"] = self.version
        # gen.variables["UnitConvert_LIBRARY_TYPE"] = "STATIC"
        # if self.options.shared:
        #   gen.variables["UnitConvert_LIBRARY_TYPE"] = "SHARED"

        if 'shared' in self.options['boost']:
            # we only want to set these if boost has the 'shared' option
            if self.options['boost'].shared:
              gen.variables["Boost_USE_STATIC_LIBS"] = "OFF"
            else:
              gen.variables["Boost_USE_STATIC_LIBS"] = "ON"

        gen.generate()

        gen = CMakeDeps(self)
        gen.generate()

        # gen = VirtualBuildEnv(self)
        # gen.generate(scope="build")

    def build(self):
        # https://docs.conan.io/en/latest/reference/conanfile/methods.html#build
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        # https://docs.conan.io/en/latest/reference/conanfile/methods.html#package
        copy(
            self,
            pattern="LICENSE.md",
            dst=os.path.join(self.package_folder, "licenses"),
            src=self.source_folder,
        )
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "cmake"))

    def package_id(self):
        self.info.shared_library_package_id()


    def package_info(self):
        self.cpp_info.libs = ["UnitConvert"]

        self.cpp_info.set_property("cmake_file_name", "UnitConvert")
        self.cpp_info.set_property(
            "cmake_target_name", "UnitConvert::UnitConvert"
        )

        # TODO: to remove in conan v2 once cmake_find_package_* generators removed
        self.cpp_info.filenames["cmake_find_package"] = "UnitConvert"
        self.cpp_info.filenames["cmake_find_package_multi"] = "UnitConvert"
        self.cpp_info.names["cmake_find_package"] = "UnitConvert"
        self.cpp_info.names["cmake_find_package_multi"] = "UnitConvert"
