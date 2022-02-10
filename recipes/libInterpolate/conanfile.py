from conans import ConanFile, CMake, tools
import os
import platform
import pathlib
import glob
import io
import re

class ConanPackage(ConanFile):
    name = "libInterpolate"
    git_url_basename = "git://github.com/CD3"
    version = "2.6"
    checkout = "2.6"

    author = "CD Clark III clifton.clark@gmail.com"
    description = "A C++ library for numerical interpolation supporting multiple methods/algorithms."
    license = "MIT"
    topics = ("C++", "Numerical Interpolation")

    generators = "cmake", "virtualenv"
    requires = 'boost/1.69.0@conan/stable', 'eigen/3.3.7@cd3/devel'

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
        cmakelists = pathlib.Path(self.name)/"CMakeLists.txt"
        cmakelists_text = cmakelists.read_text()
        if not re.search("ARCH_INDEPENDENT",cmakelists_text):
          tools.replace_in_file(str(cmakelists),
          "COMPATIBILITY SameMajorVersion",
          "COMPATIBILITY SameMajorVersion\nARCH_INDEPENDENT")

    def build(self):
        if not self.develop:
          tools.replace_in_file(os.path.join(self.name, 'CMakeLists.txt'),
                                'project(libInterpolate)',
                                'project(libInterpolate)\nset(STANDALONE OFF)')
        cmake = CMake(self)
        if not self.develop:
          cmake.definitions["BUILD_TESTS"] = "OFF"
        cmake.configure(source_folder=self.name)
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        
    def package_info(self):
        self.env_info.libInterpolate_DIR = os.path.join(self.package_folder, "cmake")
        self.env_info.libInterp_DIR = os.path.join(self.package_folder, "cmake")

