cmake_minimum_required(VERSION 3.1)

project(ConanPackageTest)
find_package(UnitConvert REQUIRED)

add_executable( example example.cpp )
target_link_libraries(example UnitConvert::UnitConvert)
