from conans import ConanFile, CMake, tools
import os, glob

class ConanPackage(ConanFile):
    name = 'UnitConvert' # Note: this line was modified to make sure this setting is static.
    git_url_basename = 'git://github.com/CD3' # Note: this line was modified to make sure this setting is static.
    version = '0.5.1' # Note: this line was modified to make sure this setting is static.
    checkout = '0.5.1' # Note: this line was modified to make sure this setting is static.

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

