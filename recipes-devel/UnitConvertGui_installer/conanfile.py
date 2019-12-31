from conans import ConanFile, CMake, tools
import os, glob, pathlib

class ConanPackage(ConanFile):
    proj_name = "UnitConvertGui"
    name = f"{proj_name}_installer"
    git_url_basename = "git://github.com/CD3"
    version = "master"
    checkout = "master"
    src_dir = f"{name}.src"

    author = "CD Clark III clifton.clark@gmail.com"
    description = "A small tool for arbitrary unit conversions."
    license = "MIT"
    topics = ("C++", "Physics")

    generators = "cmake", "virtualenv", "virtualrunenv"
    requires = 'UnitConvert/0.6@cd3/devel', 'qt/5.13.2@bincrafters/stable', 'zlib/1.2.11@conan/stable', 'bzip2/1.0.6@conan/stable'
    default_options = {'qt:qtdeclarative':True,'qt:qtquickcontrols2':True}


    settings = "os", "compiler", "build_type", "arch"

    def source(self):
        self.run(f"git clone {self.git_url_basename}/{self.proj_name}")
        self.run(f"cd {self.proj_name} && git checkout {self.checkout} && git log -1")
        pathlib.Path(f"{self.proj_name}").rename(f"{self.src_dir}")

    def build(self):
        cmake = CMake(self)
        defs = {}
        cmake.configure(source_folder=self.src_dir,defs=defs)
        cmake.build()

    def package(self):
      self.copy(self.proj_name, dst="bin")
