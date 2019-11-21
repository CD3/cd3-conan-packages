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

    requires = "boost/1.69.0@conan/stable"

    default_options = {"boost:shared":True, "mpi":False}

    def source(self):
        vmajor, vminor, vpatch = self.version.split(".")
        tools.get(
            f"https://dakota.sandia.gov/sites/default/files/distributions/public/dakota-{vmajor}.{vminor}-release-public.src.tar.gz"
        )

        next(pathlib.Path(".").glob("dakota-*.src")).rename("dakota.src")

    def build(self):
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

        cmake.configure(source_folder="dakota.src", defs=defs)
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.env_info.path.append(os.path.join(self.package_folder, "bin"))
        self.env_info.path.append(os.path.join(self.package_folder, "share","dakota","test"))
        self.env_info.PYTHON_PATH.append( os.path.join(self.package_folder, "share", "dakota", "Python") )
