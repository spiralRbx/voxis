cmake_minimum_required(VERSION 3.20)
project(voxis_core LANGUAGES NONE)

find_package(Python REQUIRED COMPONENTS Interpreter)
include(CheckLanguage)
check_language(CXX)

if(CMAKE_CXX_COMPILER)
    enable_language(CXX)

    set(CMAKE_CXX_STANDARD 17)
    set(CMAKE_CXX_STANDARD_REQUIRED ON)
    set(CMAKE_CXX_EXTENSIONS OFF)

    find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)
    find_package(pybind11 CONFIG REQUIRED)

    pybind11_add_module(_voxis_core cpp/src/bindings.cpp)
    target_include_directories(_voxis_core PRIVATE cpp/include)

    if(MSVC)
        target_compile_options(_voxis_core PRIVATE /O2 /EHsc /permissive- /DNOMINMAX)
    else()
        target_compile_options(_voxis_core PRIVATE -O3)
    endif()

    install(TARGETS _voxis_core DESTINATION voxis)
else()
    message(WARNING "No C++ compiler found. Building Voxis without the optional native extension.")
endif()
