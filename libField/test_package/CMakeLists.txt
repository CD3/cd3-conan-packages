cmake_minimum_required(VERSION 3.1)

find_package(libField REQUIRED)

add_executable( example example.cpp )
target_link_libraries(example libField::Field)
