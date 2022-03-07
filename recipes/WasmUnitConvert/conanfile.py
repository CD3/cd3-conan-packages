from conans import ConanFile, CMake, tools
import os
import platform
import pathlib
import glob
import io
import re

class ConanPackage(ConanFile):
    name = "WasmUnitConvert"
    git_url_basename = "git://github.com/CD3"
    version = "0.13"
    checkout = "0.13"
    url = "https://github.com/CD3/cd3-conan-packages"

    author = "CD Clark III clifton.clark@gmail.com"
    description = "A C++ library for runtime unit conversions compiled to WASM for use in web apps."
    license = "MIT"
    topics = ("C++", "Physics")

    generators = "cmake", "virtualenv"
    requires = 'boost/1.69.0'
    default_options = {
        'boost:header_only': True,
        }
    settings = "build_type"

    @property
    def git_url(self):
      return f"{self.git_url_basename}/UnitConvert"

    def build_requirements(self):
        # we need a recent version of cmake to build. check if it is installed,
        # and add it to the build_requires if not
        cmake_min_version = "3.14.0"
        cmake_req_version = "3.16.0"
        need_cmake = False

        if tools.which("cmake") is None:
          need_cmake = True
        else:
          output = io.StringIO()
          self.run("cmake --version",output=output)
          version = re.search( "cmake version (?P<version>\S*)", output.getvalue())
          if tools.Version( version.group("version") ) < cmake_min_version:
            need_cmake = True

        if need_cmake:
          self.build_requires(f"cmake_installer/{cmake_req_version}@conan/stable")

    def source(self):
        self.run(f"git clone {self.git_url}")
        self.run(f"cd UnitConvert && git checkout {self.checkout} && git log -1")

    def build(self):
        self.run("emcmake cmake -G 'Unix Makefiles' -DBUILD_UNIT_TESTS=OFF UnitConvert/wasm/WasmUnitConvert")
        self.run("emmake make WasmUnitConvert")


    def package(self):
      self.copy("*.js")
      self.copy("*.wasm")

        
    def package_info(self):
        self.env_info.UnitConvert_DIR = os.path.join(self.package_folder, "cmake")
        self.cpp_info.libs = ['UnitConvert']

