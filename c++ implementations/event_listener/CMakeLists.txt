cmake_minimum_required(VERSION 3.14)
project(key_processor_cpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_subdirectory(pybind11)

pybind11_add_module(key_processor_cpp
    py_bindings.cpp
    key_processor.cpp
)

target_link_libraries(key_processor_cpp PRIVATE pybind11::embed)