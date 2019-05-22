from conans import ConanFile, CMake, tools
import os

class ConanPackage(ConanFile):
    name = "libIntegrate"
    remote_url_basename = "git://github.com/CD3"
    version = "master"
    checkout = "master"

    author = "CD Clark III clifton.clark@gmail.com"
    description = "A C++ library for numerical integration supporting multiple methods/algorithms."
    license = "MIT"
    topics = ("C++", "Numerical Integration")

    generators = "cmake", "virtualenv"
    requires = 'boost/1.69.0@conan/stable'
    build_requires = 'cmake_installer/3.13.0@conan/stable'

    def source(self):
        self.run(f"git clone {self.remote_url_basename}/{self.name}")
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
        self.env_info.libIntegrate_DIR = os.path.join(self.package_folder, "cmake")

