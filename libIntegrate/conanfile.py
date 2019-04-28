from conans import ConanFile, CMake, tools
import os

class ConanPackage(ConanFile):
    name = "libIntegrate"
    remote_url_basename = "https://github.com/CD3"
    version = "master"

    author = "CD Clark III clifton.clark@gmail.com"
    description = "A C++ library for numerical integration supporting multiple methods/algorithms."
    license = "MIT"
    topics = ("C++", "Numerical Integration")

    generators = "cmake", "virtualenv"
    requires = 'boost/1.69.0@conan/stable'
    build_requires = 'cmake_installer/3.13.0@conan/stable'

    def source(self):
        self.run("git clone {REMOTE_URL}/libIntegrate".format(REMOTE_URL=self.remote_url_basename))
        self.run("cd libIntegrate && git checkout {VERSION}".format(VERSION=self.version))

    def build(self):
        tools.replace_in_file('libIntegrate/CMakeLists.txt',
                              'project(libIntegrate)',
                              'project(libIntegrate)\nset(STANDALONE OFF)')
        cmake = CMake(self)
        cmake.configure(source_folder="libIntegrate")
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        
    def package_info(self):
        self.env_info.libIntegrate_DIR = os.path.join(self.package_folder, "cmake")

