from conans import ConanFile, CMake
import os
class Test(ConanFile):
  generators = "virtualenv"

  def build(self):
    cmake = CMake(self)
    cmake.configure()
    cmake.build()

  def test(self):
    self.run("./example")
