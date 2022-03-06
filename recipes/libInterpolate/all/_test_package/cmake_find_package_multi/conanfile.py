from conans import ConanFile, CMake, tools
import os, platform, io, re
class Test(ConanFile):
  generators = "cmake_find_package_multi"
  settings = "build_type"

  def build_requirements(self):
    self.tool_requires(f"cmake/[>3.16.0]")

  def build(self):
    cmake = CMake(self)
    cmake.configure()
    cmake.build()

  def test(self):
    if platform.system() == "Windows":
        self.run(".\Debug\example.exe")
    else:
        self.run("./example")
