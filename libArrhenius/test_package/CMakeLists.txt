cmake_minimum_required(VERSION 3.10)
project(libArrheniusPackageTest CXX)

find_package(libArrhenius REQUIRED)
add_executable(example example.cpp)
target_link_libraries(example libArrhenius::Arrhenius)
