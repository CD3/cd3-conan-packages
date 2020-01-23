from conans import ConanFile, CMake, tools
import os
import platform
import pathlib
import glob
import io
import re

class ConanPackage(ConanFile):
    name = "libGBP"
    git_url_basename = "git://github.com/CD3"
    version = "0.1.1"
    checkout = "v0.1.1"

    author = "CD Clark III clifton.clark@gmail.com"
    description = "A C++ library Gaussian bean propagation calculations."
    license = "MIT"
    topics = ("C++", "Physics")

    generators = "cmake", "virtualenv"
    requires = 'boost/1.69.0@conan/stable', 'eigen/3.3.7@cd3/devel'
    settings = "os", "compiler", "build_type", "arch"

    @property
    def git_url(self):
      return f"{self.git_url_basename}/{self.name}"

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
        self.run(f"cd {self.name} && git checkout {self.checkout} && git log -1")

    def build(self):
        # this will disable unit tests
        tools.replace_in_file(os.path.join(self.source_folder, self.name, 'CMakeLists.txt'),"  set(STANDALONE ON)","  set(STANDALONE OFF)")
        cmake = CMake(self)
        defs = {}
        print(defs)
        cmake.configure(source_folder=self.name,defs=defs)
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        
    def package_info(self):
        self.env_info.libGBP_DIR = os.path.join(self.package_folder, "cmake")

