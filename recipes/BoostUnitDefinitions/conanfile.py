from conans import ConanFile, CMake, tools
import os, glob

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

    def build_requirements(self):
        # we need cmake to build. check if it is installed,
        # and add it to the build_requires if not
        if tools.which("cmake") is None:
            self.build_requires("cmake_installer/3.16.0@conan/stable")

    def source(self):
        self.run(f"git clone {self.git_url_basename}/{self.name}")
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

