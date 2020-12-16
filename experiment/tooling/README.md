# Experimental Conan-based Tooling

Some experimental scripts for using conan to perform automated integration testing, generating conan recipe instances from baseline recipes, etc.

For example, `export-tool.py` can generate and export instances of package recipes from a baseline recipe. Here an "instance" means a copy of a package recipe with settings overwritten.
This can be useful for quickly exporting recipes for multiple versions of a library.

`test-integrations.py` can test that the latest versions (or some set of specified version) can build against each other.

