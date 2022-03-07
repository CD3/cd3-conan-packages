from conans import ConanFile, CMake, tools
import os, platform, io, re
class Test(ConanFile):
  generators = "compiler_args"

  def build(self):
    self.run("g++ ../../example.cpp -o example @conanbuildinfo.args")

  def test(self):
    self.run("./example")
