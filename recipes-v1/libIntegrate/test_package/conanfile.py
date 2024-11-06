from conans import ConanFile, CMake, tools
import os, platform, io, re
class Test(ConanFile):
  generators = "virtualenv"

  def build_requirements(self):
    if tools.which("cmake") is None:
      self.build_requires("cmake_installer/3.16.0@conan/stable")
    else:
      output = io.StringIO()
      self.run("cmake --version",output=output)
      version = re.search( "cmake version (?P<version>\S*)", output.getvalue())
      if tools.Version( version.group("version") ) < "3.12.0":
        self.build_requires("cmake_installer/3.16.0@conan/stable")

  def build(self):
    cmake = CMake(self)
    cmake.configure()
    cmake.build()

  def test(self):
    if platform.system() == "Windows":
        self.run(".\Debug\example.exe")
    else:
        self.run("./example")
