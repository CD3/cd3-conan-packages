from conans import ConanFile, CMake, tools
import os
import platform
import pathlib
import glob
import io
import re

class ConanPackage(ConanFile):
    name = "hdf5"
    version = "1.10.5"
    url = "https://github.com/CD3/cd3-conan-packages"
    description = "HDF5 C and C++ libraries"
    license = "https://support.hdfgroup.org/ftp/HDF5/releases/COPYING"
    generators = "cmake", "virtualenv"
    settings = "os", "compiler", "build_type", "arch"

    requires = "zlib/1.2.11"

    options = {
        "cxx": [True,False],
        "shared": [True,False],
        "parallel": [True,False],
        }
    default_options = (
        "cxx=True",
        "shared=False",
        "parallel=False",
        "zlib:shared=False"
    )

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
      vmajor,vminor,vpatch = self.version.split(".")
      tools.get(f"https://support.hdfgroup.org/ftp/HDF5/releases/hdf5-{vmajor}.{vminor}/hdf5-{vmajor}.{vminor}.{vpatch}/src/hdf5-{vmajor}.{vminor}.{vpatch}.tar.gz")

      next(pathlib.Path('.').glob('hdf5-*')).rename("hdf5")


    def build(self):
        cmake = CMake(self)
        defs = dict()

        defs['BUILD_SHARED_LIBS']  = "ON" if self.options.shared else "OFF"   # Build Shared Libraries
        defs['BUILD_STATIC_EXECS'] = "OFF"  # Build Static Executables
        defs['BUILD_TESTING']      = "OFF"  # Build HDF5 Unit Testing

        defs['HDF5_BUILD_CPP_LIB']  = "ON" if self.options.cxx else "OFF"    # Build HDF5 C++ Library
        defs['HDF5_BUILD_EXAMPLES'] = "OFF" # Build HDF5 Library Examples
        defs['HDF5_BUILD_FORTRAN']  = "OFF" # Build FORTRAN support
        defs['HDF5_BUILD_JAVA']     = "OFF" # Build JAVA support
        defs['HDF5_BUILD_HL_LIB']   = "ON"  # Build HIGH Level HDF5 Library
        defs['HDF5_BUILD_TOOLS']    = "ON"  # Build HDF5 Tools

        # These options are listed in the hdf5 cmake documentation. Not
        # sure if we should mess with them or now...
        # defs['ALLOW_UNSUPPORTED']              = "OFF"   # Allow unsupported combinations of configure options
        # defs['HDF5_EXTERNAL_LIB_PREFIX']       = ""      # Use prefix for custom library naming.
        # defs['HDF5_DISABLE_COMPILER_WARNINGS'] = "OFF"   # Disable compiler warnings
        # defs['HDF5_ENABLE_ALL_WARNINGS']       = "OFF"   # Enable all warnings
        # defs['HDF5_ENABLE_CODESTACK']          = "OFF"   # Enable the function stack tracing (for developer debugging).
        # defs['HDF5_ENABLE_COVERAGE']           = "OFF"   # Enable code coverage for Libraries and Programs
        # defs['HDF5_ENABLE_DEBUG_APIS']         = "OFF"   # Turn on extra debug output in all packages
        # defs['HDF5_ENABLE_DEPRECATED_SYMBOLS'] = "ON"    # Enable deprecated public API symbols
        # defs['HDF5_ENABLE_DIRECT_VFD']         = "OFF"   # Build the Direct I/O Virtual File Driver
        # defs['HDF5_ENABLE_EMBEDDED_LIBINFO']   = "ON"    # embed library info into executables
        # defs['HDF5_ENABLE_HSIZET']             = "ON"    # Enable datasets larger than memory
        defs['HDF5_ENABLE_PARALLEL']           = "ON" if self.options.parallel else "OFF"   # Enable parallel build (requires MPI)
        # defs['HDF5_ENABLE_PREADWRITE']         = "ON"    # Use pread/pwrite in sec2/log/core VFDs in place of read/write (when available)
        # defs['HDF5_ENABLE_TRACE']              = "OFF"   # Enable API tracing capability
        # defs['HDF5_ENABLE_USING_MEMCHECKER']   = "OFF"   # Indicate that a memory checker is used
        # defs['HDF5_GENERATE_HEADERS']          = "ON"    # Rebuild Generated Files
        # defs['HDF5_BUILD_GENERATORS']          = "OFF"   # Build Test Generators
        # defs['HDF5_JAVA_PACK_JRE']             = "OFF"   # Package a JRE installer directory
        # defs['HDF5_MEMORY_ALLOC_SANITY_CHECK'] = "OFF"   # Indicate that internal memory allocation sanity checks are enabled
        # defs['HDF5_NO_PACKAGES']               = "OFF"   # Do not include CPack Packaging
        # defs['HDF5_PACK_EXAMPLES']             = "OFF"   # Package the HDF5 Library Examples Compressed File
        # defs['HDF5_PACK_MACOSX_FRAMEWORK']     = "OFF"   # Package the HDF5 Library in a Frameworks
        # defs['HDF5_BUILD_FRAMEWORKS']          = "FALSE" # TRUE to build as frameworks libraries,
                                                         # # FALSE to build according to BUILD_SHARED_LIBS
        # defs['HDF5_PACKAGE_EXTLIBS']           = "OFF"   # CPACK - include external libraries
        # defs['HDF5_STRICT_FORMAT_CHECKS']      = "OFF"   # Whether to perform strict file format checks
        # defs['HDF_TEST_EXPRESS']               = "0"     # Control testing framework (0-3)
        # defs['HDF5_TEST_VFD']                  = "OFF"   # Execute tests with different VFDs
        # defs['HDF5_USE_16_API_DEFAULT']        = "OFF"   # Use the HDF5 1.6.x API by default
        # defs['HDF5_USE_18_API_DEFAULT']        = "OFF"   # Use the HDF5 1.8.x API by default
        # defs['HDF5_USE_110_API_DEFAULT']       = "OFF"   # Use the HDF5 1.10.x API by default
        # defs['HDF5_USE_112_API_DEFAULT']       = "ON"    # Use the HDF5 1.12.x API by default
        # defs['HDF5_USE_FOLDERS']               = "ON"    # Enable folder grouping of projects in IDEs.
        # defs['HDF5_WANT_DATA_ACCURACY']        = "ON"    # IF data accuracy is guaranteed during data conversions
        # defs['HDF5_WANT_DCONV_EXCEPTION']      = "ON"    # exception handling functions is checked during data conversions
        # defs['HDF5_ENABLE_THREADSAFE']         = "OFF"   # Enable Threadsafety
  # if (APPLE)
      # HDF5_BUILD_WITH_INSTALL_NAME "Build with library install_name set to the installation path"  OFF
  # if (CMAKE_BUILD_TYPE MATCHES Debug)
      # HDF5_ENABLE_INSTRUMENT     "Instrument The library"                      OFF
  # if (HDF5_TEST_VFD)
      # HDF5_TEST_FHEAP_VFD        "Execute fheap test with different VFDs"      ON

       # defs['HDF5_ALLOW_EXTERNAL_SUPPORT'] = "NO"   # Allow External Library Building
       # defs['HDF5_ENABLE_SZIP_SUPPORT']    = "OFF"  # Use SZip Filter
       # defs['HDF5_ENABLE_Z_LIB_SUPPORT']   = "OFF"  # Enable Zlib Filters
       # defs['ZLIB_USE_EXTERNAL']           = "0"    # Use External Library Building for ZLIB
       # defs['SZIP_USE_EXTERNAL']           = "0"    # Use External Library Building for SZIP
  # if (HDF5_ENABLE_SZIP_SUPPORT)
      # HDF5_ENABLE_SZIP_ENCODING "Use SZip Encoding"      OFF
  # if (WINDOWS)
      # H5_DEFAULT_PLUGINDIR    "%ALLUSERSPROFILE%/hdf5/lib/plugin"
  # else ()
      # H5_DEFAULT_PLUGINDIR    "/usr/local/hdf5/lib/plugin"
  # endif ()


        cmake.configure(source_folder="hdf5", defs=defs)
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        
    def package_info(self):
        self.env_info.hdf5_DIR = os.path.join(self.package_folder, "share", "cmake", "hdf5")

