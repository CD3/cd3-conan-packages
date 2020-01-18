from conans import ConanFile, CMake, tools
import os, glob, io, re

class ConanPackage(ConanFile):
    name = "BoostUnitDefinitions"
    git_url_basename = "git://github.com/CD3"
    version = "0.1.2"
    checkout = "0.1.2"

    author = "CD Clark III clifton.clark@gmail.com"
    description = "A set of unit definitions for doing physical calculations with Boost.Units."
    license = "MIT"
    topics = ("C++", "Physics")

    generators = "cmake_paths", "virtualenv"
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
        defs = {}
        if not self.develop:
          defs['BUILD_UNIT_TESTS'] = False
        cmake.configure(source_folder=self.name,defs=defs)
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        
    def package_info(self):
        self.env_info.BoostUnitDefinitions_DIR = os.path.join(self.package_folder, "cmake")

