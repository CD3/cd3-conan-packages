# AUTO
# NOSTDOUT
reset
cd demo_sandbox
# STDOUT
# INSERT
cmake
conan
ls
git clone https://github.com/CD3/cd3-conan-packages
cd cd3-conan-packages
python install.py
cd ..
ls
cd integrator
cat main.cpp


cat CMakeLists.txt


nano conanfile.py
from conans import ConanFile, CMake

class ConanBuild(ConanFile):
    generators = "cmake", "virtualenv"
    requires = 'libField/master@cd3/devel','libIntegrate/master@cd3/devel','libInterpolate/master@cd3/devel'
    build_requires = 'cmake_installer/3.13.0@conan/stable'


    def build(self):
      cmake = CMake(self)
      cmake.configure()
      cmake.build()



mkdir build
cd build
conan install .. --build missing
ls
conan build ..
ls
./compute-integral


