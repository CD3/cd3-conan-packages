from conans import ConanFile, CMake, tools
import os

class TestConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake", "virtualenv"
    requires = 'libInterpolate/master@local/testing'
    build_requires = 'cmake_installer/3.13.0@conan/stable'

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        self.run(".%sexample" % os.sep)
