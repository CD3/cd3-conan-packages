import os

from conan import ConanFile
from conan.tools.files import copy, get


class libfieldRecipe(ConanFile):
    name = "libfield"
    # No settings/options are necessary, this is header only
    exports_sources = "include/*"
    # We can avoid copying the sources to the build folder in the cache
    no_copy_source = True

    def requirements(self):
        self.requires("boost/1.86.0")

    def layout(self):
        self.cpp.source.includedirs = ["src"]

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        # This will also copy the "include" folder
        copy(
            self, "*.hpp", os.path.join(self.source_folder, "src"), self.package_folder
        )

    def package_info(self):
        # For header-only packages, libdirs and bindirs are not used
        # so it's necessary to set those as empty.
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.includedirs = [""]
        self.cpp_info.set_property("cmake_file_name", "libField")
        self.cpp_info.set_property("cmake_target_name", "libField::Field")
