from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain
from conan.tools.files import get,copy, replace_in_file
import pathlib

class ConanPackage(ConanFile):
    name = "unitconvert"

    author = "CD Clark III clifton.clark@gmail.com"
    description = "A C++ library for runtime unit conversions."
    license = "MIT"
    topics = ("C++", "physics", "dimensional analysis", "unit conversions")
    url = "https://github.com/CD3/cd3-conan-packages"
    settings = "os", "compiler", "build_type", "arch"

    requires = 'boost/1.72.0'

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    def source(self):
        get(self,**self.conan_data["sources"][self.version], strip_root=True, destination=self._source_subfolder)
        replace_in_file(self, f"{self._source_subfolder}/CMakeLists.txt", 'set_target_properties( ${LIB_NAME} PROPERTIES DEBUG_POSTFIX "-d" )', "")


    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions['BUILD_UNIT_TESTS'] = False
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

