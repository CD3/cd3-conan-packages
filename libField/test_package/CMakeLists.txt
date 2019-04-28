cmake_minimum_required(VERSION 3.10)
project(libFieldPackageTest CXX)

find_package(libField REQUIRED)
add_executable(example example.cpp)
target_link_libraries(example libField::Field)
