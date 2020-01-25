from conans import ConanFile, CMake, tools
import os
import platform
import pathlib
import glob
import io
import re

class ConanPackage(ConanFile):
    name = "libField"
    git_url_basename = "git://github.com/CD3"
    version = "0.7.1"
    checkout = "0.7.1"

    author = "CD Clark III clifton.clark@gmail.com"
    description = "A C++ library for storing and working with field data."
    license = "MIT"
    topics = ("C++", "Physics")

    generators = "cmake", "virtualenv"
    requires = 'boost/1.69.0@conan/stable', 'hdf5/1.10.5@cd3/devel', 'zlib/1.2.11'

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
          tools.replace_in_file(os.path.join(self.source_folder, self.name, 'CMakeLists.txt'),
                                f'project({self.name})',
                                f'project({self.name})\nset(STANDALONE OFF)')
        cmake = CMake(self)
        cmake.configure(source_folder="libField")
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        
    def package_info(self):
        self.env_info.libField_DIR = os.path.join(self.package_folder, "cmake")

