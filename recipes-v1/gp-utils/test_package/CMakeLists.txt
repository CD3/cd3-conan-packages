cmake_minimum_required(VERSION 3.1)

project(ConanPackageTest)
find_package(gputils REQUIRED)

add_executable( example example.cpp )
target_link_libraries(example gputils::gputils)
