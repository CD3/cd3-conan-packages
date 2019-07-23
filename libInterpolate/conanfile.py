from conans import ConanFile, CMake, tools
import os

class ConanPackage(ConanFile):
    name = "libInterpolate"
    git_url_basename = "git://github.com/CD3"
    version = "master"
    checkout = "master"

    author = "CD Clark III clifton.clark@gmail.com"
    description = "A C++ library for numerical interpolation supporting multiple methods/algorithms."
    license = "MIT"
    topics = ("C++", "Numerical Interpolation")

    generators = "cmake", "virtualenv"
    requires = 'boost/1.69.0@conan/stable', 'eigen/3.3.7@conan/stable'
    build_requires = 'cmake_installer/3.13.0@conan/stable'
    settings = "os", "compiler", "build_type", "arch"

    def source(self):
        self.run(f"git clone {self.git_url_basename}/{self.name}")
        self.run(f"cd {self.name} && git checkout {self.checkout} && git log -1")

    def build(self):
        if not self.develop:
          tools.replace_in_file(os.path.join(self.name, 'CMakeLists.txt'),
                                'project(libInterp)',
                                'project(libInterp)\nset(STANDALONE OFF)')
        cmake = CMake(self)
        defs = {}
        cmake.configure(source_folder=self.name,defs=defs)
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        
    def package_info(self):
        self.env_info.libInterpolate_DIR = os.path.join(self.package_folder, "cmake")
        self.env_info.libInterp_DIR = os.path.join(self.package_folder, "cmake")

