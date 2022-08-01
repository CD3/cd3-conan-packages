from conans import ConanFile
from conan.tools.cmake import CMake
import os, io, re, platform
class Test(ConanFile):
  settings = "os","compiler","arch","build_type"
  generators = "CMakeDeps","CMakeToolchain"


  def build(self):
    cmake = CMake(self)
    cmake.configure()
    cmake.build()

  def test(self):
    if platform.system() == "Windows":
        self.run(".\Debug\example.exe")
    else:
        self.run("./example")
