from conans import ConanFile, CMake, tools
import os, glob

class ConanPackage(ConanFile):
    name = "UnitConvert"
    remote_url_basename = "https://github.com/CD3"
    version = "master"

    author = "CD Clark III clifton.clark@gmail.com"
    description = "A C++ library for runtime unit conversions."
    license = "MIT"
    topics = ("C++", "Physics")

    generators = "cmake", "virtualenv"
    requires = 'boost/1.69.0@conan/stable'
    build_requires = 'cmake_installer/3.13.0@conan/stable'

    def source(self):
        self.run("git clone {REMOTE_URL}/UnitConvert".format(REMOTE_URL=self.remote_url_basename))
        self.run("cd UnitConvert&& git checkout {VERSION}".format(VERSION=self.version))

    def build(self):
        cmake = CMake(self)

        defs = {}
        defs["BUILD_UNIT_TESTS"] = "OFF"
        cmake.configure(defs=defs,source_folder="UnitConvert")

        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        
    def package_info(self):
        self.env_info.UnitConvert_DIR = os.path.join(self.package_folder, "cmake")

