from conans import ConanFile, CMake
import os, platform
class Test(ConanFile):
  generators = "virtualenv"

  def build(self):
    cmake = CMake(self)
    cmake.configure()
    cmake.build()

  def test(self):
    if platform.system() == "Windows":
        self.run(".\Debug\example.exe")
    else:
        self.run("./example")
