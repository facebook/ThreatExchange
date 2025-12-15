# CMake to build the Python binding for vpdq. This is built with the Python
# scikit-build-core build backend. This compiles vpdq and compiles the Cython
# and then links vpdq to the compiled Cython.

cmake_minimum_required(VERSION 3.15...3.30)
project(${SKBUILD_PROJECT_NAME} LANGUAGES CXX)

set(CMAKE_CXX_STANDARD
    14
    CACHE STRING "C++ version selection")
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Compile pdq and vpdq to produce their library files.
add_subdirectory(cpp)

# Build the Cython bindings. Create the cpp file from the Cython pyx file,
# compile it, and link it to vpdq.

find_package(
  Python
  COMPONENTS Interpreter Development.Module
  REQUIRED)

add_custom_command(
  OUTPUT ${CMAKE_CURRENT_SOURCE_DIR}/python/vpdq.cpp
  COMMENT
    "Making ${CMAKE_CURRENT_BINARY_DIR}/python/vpdq.cpp from ${CMAKE_CURRENT_SOURCE_DIR}/python/vpdq.pyx"
  COMMAND
    Python::Interpreter -m cython --cplus "${CMAKE_CURRENT_SOURCE_DIR}/python/vpdq.pyx"
    --output-file "${CMAKE_CURRENT_SOURCE_DIR}/python/vpdq.cpp"
  DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/python/vpdq.pyx
  VERBATIM)

python_add_library(vpdq MODULE ${CMAKE_CURRENT_SOURCE_DIR}/python/vpdq.cpp
                   WITH_SOABI)

# Link pdq and vpdq to the vpdq Cython library
target_link_libraries(vpdq PUBLIC pdqlib)
target_link_libraries(vpdq PUBLIC vpdqlib)

# Note: The install directory determines the module directory. For example, if
# it's changed to 'foo', then in python you would have to do 'from foo import
# vpdq' to use the module. Leaving it at '.' allows for just 'import vpdq'.
install(TARGETS vpdq DESTINATION .)
