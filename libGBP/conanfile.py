from conans import ConanFile, CMake, tools
import os

class ConanPackage(ConanFile):
    name = "libGBP"
    remote_url_basename = "https://github.com/CD3"
    version = "master"

    author = "CD Clark III clifton.clark@gmail.com"
    description = "A C++ library Gaussian bean propagation calculations."
    license = "MIT"
    topics = ("C++", "Physics")

    generators = "cmake", "virtualenv"
    requires = 'boost/1.69.0@conan/stable', 'eigen/3.3.7@conan/stable'
    build_requires = 'cmake_installer/3.13.0@conan/stable'

    def source(self):
        self.run("git clone {REMOTE_URL}/libGBP".format(REMOTE_URL=self.remote_url_basename))
        self.run("cd libGBP && git checkout {VERSION}".format(VERSION=self.version))

    def build(self):
        tools.replace_in_file('libGBP/CMakeLists.txt',
                              'project(libGBP)',
                              'project(libGBP)\nset(STANDALONE OFF)')
        cmake = CMake(self)
        defs = {}
        defs['Eigen3_DIR'] = os.path.join(self.deps_cpp_info["eigen"].rootpath,"share","eigen3","cmake")
        print(defs)
        cmake.configure(defs=defs,source_folder="libGBP")
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        
    def package_info(self):
        self.env_info.libGBP_DIR = os.path.join(self.package_folder, "cmake")
        self.env_info.Eigen3_DIR = os.path.join(self.deps_cpp_info["eigen"].rootpath,"share","eigen3","cmake")

