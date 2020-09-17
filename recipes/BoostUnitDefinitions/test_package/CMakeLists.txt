cmake_minimum_required(VERSION 3.1)

project(ConanPackageTest)
include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()
find_package(BoostUnitDefinitions REQUIRED)
find_package(Boost REQUIRED)

add_executable( example example.cpp )
target_link_libraries(example BoostUnitDefinitions::BoostUnitDefinitions Boost::boost)
