from conans import ConanFile, CMake, tools
import os, io, re, platform
class Test(ConanFile):
  generators = "CMakeDeps", "CMakeToolchain"
  settings = 'build_type', 'os', 'arch', 'compiler'


  def requirements(self):
      self.requires("boost/1.71.0")

  def build(self):
    cmake = CMake(self)
    cmake.configure()
    cmake.build()

  def test(self):
    if platform.system() == "Windows":
        self.run(".\Debug\example.exe")
    else:
        self.run("./example")
