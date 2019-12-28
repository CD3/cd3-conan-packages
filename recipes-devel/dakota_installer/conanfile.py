from conans import ConanFile, CMake, tools
import os, pathlib


class ConanPackage(ConanFile):
    # define injected name and version
    # so that the export.py script overwrite
    # them instead of the name and version vars
    injected_name = "ignore"
    injected_version = "ignore"
    name = "dakota_installer"
    version = "6.10.0"
    description = "dakota software suite"
    generators = "virtualenv"
    settings = "os", "compiler", "build_type", "arch"
    options = {"mpi" : [True,False] }

    requires = "boost/1.66.0@conan/stable", "lapack/3.7.1@conan/stable"

    default_options = {"mpi":False}

    def source(self):
        vmajor, vminor, vpatch = self.version.split(".")
        tools.get(
            f"https://dakota.sandia.gov/sites/default/files/distributions/public/dakota-{vmajor}.{vminor}-release-public.src.tar.gz"
        )

        next(pathlib.Path(".").glob("dakota-*.src")).rename("dakota.src")

    def build(self):
        # dakota tries to find system installs for blas and lapack with find_library(...) first
        # if it does not find them, it then calls find_package(...)
        # we want to make sure the conan package version is used, so we need to remove the system library checks
        cmakefile = pathlib.Path(self.source_folder) / "dakota.src/CMakeLists.txt"
        tools.replace_in_file(str(cmakefile), f'find_library(BLAS_LIBS blas)','')
        tools.replace_in_file(str(cmakefile), f'find_library(LAPACK_LIBS lapack)','')
        cmake = CMake(self)
        defs = dict()
        # these options are listed in Dakota's build
        # instructions. they only need to be set if the
        # defaults are not sufficient
        # defs['BLAS_LIBS'] = "/usr/lib64/libblas.so"
        # defs['LAPACK_LIBS'] = "/usr/lib64/liblapack.so"
        defs['DAKOTA_HAVE_MPI'] = self.options.mpi
        # defs['MPI_CXX_COMPILER'] = "/path/to/mpicxx"
        # defs['Trilinos_DIR'] = "/path/to/Trilinos/install"
        defs['CMAKE_INSTALL_PREFIX'] = self.package_folder
        # make sure cmake can find the conan-installed lapack
        defs['LAPACK_DIR'] = next((pathlib.Path(self.deps_cpp_info['lapack'].rootpath) / "lib/cmake/").glob("lapack-*"))

        cmake.configure(source_folder="dakota.src", defs=defs)
        cmake.build()

    def package(self):
        # cmake = CMake(self)
        # cmake.install()
        # cmake will strip rpath, which is not what we want
        self.copy("*.lib", dst="lib", keep_path=False)
        self.copy("*.dll", dst="bin", keep_path=False)
        self.copy("*.so", dst="lib", keep_path=False)
        self.copy("*.dylib", dst="lib", keep_path=False)

        self.copy("*/coliny", dst="bin", keep_path=False)
        self.copy("*/dakota", dst="bin", keep_path=False)
        self.copy("*/dakota.input.nspec", dst="bin", keep_path=False)
        self.copy("*/dakota.input.summary", dst="bin", keep_path=False)
        self.copy("*/dakota_library_mode", dst="bin", keep_path=False)
        self.copy("*/dakota_order_input", dst="bin", keep_path=False)
        self.copy("*/dakota_restart_util", dst="bin", keep_path=False)
        self.copy("*/dakota.sh", dst="bin", keep_path=False)
        self.copy("*/dakota.xml", dst="bin", keep_path=False)
        self.copy("*/dakota.xsd", dst="bin", keep_path=False)
        self.copy("*/dprepro", dst="bin", keep_path=False)
        self.copy("*/dprepro.perl", dst="bin", keep_path=False)
        self.copy("*/fsu_cvt_standalone", dst="bin", keep_path=False)
        self.copy("*/fsu_halton_standalone", dst="bin", keep_path=False)
        self.copy("*/fsu_hammersley_standalone", dst="bin", keep_path=False)
        self.copy("*/fsu_latinize_standalone", dst="bin", keep_path=False)
        self.copy("*/fsu_quality_standalone", dst="bin", keep_path=False)
        self.copy("*/lhsdrv", dst="bin", keep_path=False)
        self.copy("*/memmon", dst="bin", keep_path=False)
        self.copy("*/mpitile", dst="bin", keep_path=False)
        self.copy("*/pyprepro", dst="bin", keep_path=False)
        self.copy("*/surfpack", dst="bin", keep_path=False)
        self.copy("*/timer", dst="bin", keep_path=False)

    def package_info(self):
        self.env_info.path.append(os.path.join(self.package_folder, "bin"))
        self.env_info.path.append(os.path.join(self.package_folder, "share","dakota","test"))
        self.env_info.PYTHON_PATH.append( os.path.join(self.package_folder, "share", "dakota", "Python") )
