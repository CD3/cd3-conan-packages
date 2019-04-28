cmake_minimum_required(VERSION 3.10)
project(libGBPPackageTest CXX)

find_package(libGBP REQUIRED)
add_executable(example example.cpp)
target_link_libraries(example libGBP::GBP)
