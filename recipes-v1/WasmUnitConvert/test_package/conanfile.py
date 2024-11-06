from conans import ConanFile, CMake, tools
import os, io, re, platform, pathlib
class Test(ConanFile):
  generators = "virtualenv"

  def build(self):
      test_exe = pathlib.Path(self.source_folder)/"test.sh"
      self.run(f"cp {str(test_exe)} .")

  def imports(self):
    self.copy("*.js")
    self.copy("*.wasm")

  def test(self):
      self.run("./test.sh")
