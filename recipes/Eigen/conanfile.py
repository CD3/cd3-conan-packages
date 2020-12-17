from conans import ConanFile, tools, CMake
import os
import platform
import pathlib
import glob
import io
import re


class ConanPackage(ConanFile):
    name = "eigen"
    version = "3.3.7"
    url = "https://github.com/conan-community/conan-eigen"
    homepage = "http://eigen.tuxfamily.org"
    description = "Eigen is a C++ template library for linear algebra: matrices, vectors, \
                   numerical solvers, and related algorithms."
    license = "Mozilla Public License Version 2.0"
    no_copy_source = True
    options = {"EIGEN_USE_BLAS": [True, False],
               "EIGEN_USE_LAPACKE": [True, False],
               "EIGEN_USE_LAPACKE_STRICT": [True, False]}
    default_options = "EIGEN_USE_BLAS=False", "EIGEN_USE_LAPACKE=False", "EIGEN_USE_LAPACKE_STRICT=False"

    @property
    def source_subfolder(self):
        return "sources"

    def build_requirements(self):
        # we need a recent version of cmake to build. check if it is installed,
        # and add it to the build_requires if not
        cmake_min_version = "3.14.0"
        cmake_req_version = "3.16.0"
        need_cmake = False

        if tools.which("cmake") is None:
          need_cmake = True
        else:
          output = io.StringIO()
          self.run("cmake --version",output=output)
          version = re.search( "cmake version (?P<version>\S*)", output.getvalue())
          if tools.Version( version.group("version") ) < cmake_min_version:
            need_cmake = True

        if need_cmake:
          self.build_requires(f"cmake_installer/{cmake_req_version}@conan/stable")

    def source(self):
        source_url = "http://gitlab.com/libeigen/eigen"
        tools.get("{0}/-/archive/{1}/eigen-{1}.tar.gz".format(source_url, self.version))
        os.rename(glob.glob("eigen-*")[0], self.source_subfolder)

    def package(self):
        cmake = CMake(self)
        cmake.configure(source_folder=self.source_subfolder)
        cmake.install()
        self.copy("COPYING.*", dst="licenses", src=self.source_subfolder,
                  ignore_case=True, keep_path=False)

    def package_info(self):
        self.cpp_info.includedirs = ['include/eigen3']
        if self.options.EIGEN_USE_BLAS:
            self.cpp_info.defines.append("EIGEN_USE_BLAS")

        if self.options.EIGEN_USE_LAPACKE:
            self.cpp_info.defines.append("EIGEN_USE_LAPACKE")

        if self.options.EIGEN_USE_LAPACKE_STRICT:
            self.cpp_info.defines.append("EIGEN_USE_LAPACKE_STRICT")

        self.env_info.Eigen3_DIR = os.path.join(self.package_folder, "share", "eigen3", "cmake")
