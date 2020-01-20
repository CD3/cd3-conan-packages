from conans import ConanFile, CMake, tools
import os
import platform
import pathlib
import glob
import io
import re

class ConanPackage(ConanFile):
    name = "libIntegrate"
    git_url_basename = "git://github.com/CD3"
    version = "0.4.2"
    checkout = "v0.4.2"

    author = "CD Clark III clifton.clark@gmail.com"
    description = "A C++ library for numerical integration supporting multiple methods/algorithms."
    license = "MIT"
    topics = ("C++", "Numerical Integration")

    generators = "cmake", "virtualenv"
    requires = 'boost/1.69.0@conan/stable'

    @property
    def git_url(self):
      return f"{self.git_url_basename}/{self.name}"

    def build_requirements(self):
        # we need a recent version of cmake to build. check if it is installed,
        # and add it to the build_requires if not
        cmake_min_version = "3.12.0"
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
        self.run(f"cd {self.name} && git checkout {self.checkout} && git log -1")


    def build(self):
        cmake = CMake(self)
        if not self.develop:
          cmake.definitions["BUILD_TESTS"] = "OFF"
        cmake.configure(source_folder=self.name)
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        
    def package_info(self):
        self.env_info.libIntegrate_DIR = os.path.join(self.package_folder, "cmake")

