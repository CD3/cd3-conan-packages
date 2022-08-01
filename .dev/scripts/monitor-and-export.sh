#! /bin/bash

# Minitor all recipes for changes, and export them when a change is detected

fd conanfile.*.py | entr conan export /_ rhd/devel
