from conans import ConanFile, CMake, tools
import os, io, re, platform
class Test(ConanFile):
  generators = "virtualenv"

  def requirements(self):
    self.requires("boost/1.70.0")
    self.requires("libInterpolate/2.3.2@cd3/devel")
    self.requires("hdf5/1.10.5@cd3/devel")

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
