cmake_minimum_required(VERSION 3.16)
project(test_package LANGUAGES CXX)

find_package(UnitConvert REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} PRIVATE UnitConvert::UnitConvert)
target_compile_features(${PROJECT_NAME} PRIVATE cxx_std_17)
