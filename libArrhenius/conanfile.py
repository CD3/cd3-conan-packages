from conans import ConanFile, CMake, tools
import os

class ConanPackage(ConanFile):
    name = "libArrhenius"
    git_url_basename = "git://github.com/CD3"
    version = "master"
    checkout = "master"

    author = "CD Clark III clifton.clark@gmail.com"
    description = "A C++ library for doing Arrhenius Integral calculations."
    license = "MIT"
    topics = ("C++", "Physics")

    generators = "cmake", "virtualenv"
    requires = 'boost/1.69.0@conan/stable', 'eigen/3.3.7@conan/stable'
    settings = "os", "compiler", "build_type", "arch"

    def source(self):
        self.run(f"git clone {self.git_url_basename}/{self.name}")
        self.run(f"cd {self.name} && git checkout {self.checkout} && git log -1")

    def build(self):
        if not self.develop:
          tools.replace_in_file(os.path.join(self.source_folder, self.name, 'CMakeLists.txt'),
                                f'project({self.name})',
                                f'project({self.name})\nset(STANDALONE OFF)')
        cmake = CMake(self)
        defs = {}
        cmake.configure(source_folder=self.name,defs=defs)
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        
    def package_info(self):
        self.env_info.libArrhenius_DIR = os.path.join(self.package_folder, "cmake")

