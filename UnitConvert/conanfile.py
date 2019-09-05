from conans import ConanFile, CMake, tools
import os, glob

class ConanPackage(ConanFile):
    name = "UnitConvert"
    git_url_basename = "git://github.com/CD3"
    version = "master"
    checkout = "master"

    author = "CD Clark III clifton.clark@gmail.com"
    description = "A C++ library for runtime unit conversions."
    license = "MIT"
    topics = ("C++", "Physics")

    generators = "cmake", "virtualenv"
    requires = 'boost/1.69.0@conan/stable'
    settings = "os", "compiler", "build_type", "arch"

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
        self.env_info.UnitConvert_DIR = os.path.join(self.package_folder, "cmake")

