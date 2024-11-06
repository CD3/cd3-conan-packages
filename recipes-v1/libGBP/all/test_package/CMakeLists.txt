cmake_minimum_required(VERSION 3.15)
project(libGBP_Tests)

find_package(libGBP REQUIRED)

add_executable( example example.cpp )
target_link_libraries( example libGBP::GBP )
