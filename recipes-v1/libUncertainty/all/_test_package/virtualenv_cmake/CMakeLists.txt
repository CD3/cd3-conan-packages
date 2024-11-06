cmake_minimum_required(VERSION 3.1)

find_package(libUncertainty REQUIRED)

add_executable( example example.cpp )
target_link_libraries(example libUncertainty::libUncertainty)
