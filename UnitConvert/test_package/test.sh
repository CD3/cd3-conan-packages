#! /bin/bash

mkdir build
cd build
conan install UnitConvert/0.5@cd3/devel -g virtualenv
veval cmake ..
cmake --build .
./example
