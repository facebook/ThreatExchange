# Top level CMake for vpdq
# This will build vpdq, pdq, and the vpdq CLI programs.

cmake_minimum_required(VERSION 3.17)

project(vpdq LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 14)

# Sanitizer build type options.
# This allows you to build with address/thread sanitizer by using
# -DCMAKE_BUILD_TYPE=Asan or Tsan on the generator.
# From https://stackoverflow.com/a/64294837
if(NOT MSVC)
get_property(isMultiConfig GLOBAL PROPERTY GENERATOR_IS_MULTI_CONFIG)

if(isMultiConfig)
    if(NOT "Asan" IN_LIST CMAKE_CONFIGURATION_TYPES)
        list(APPEND CMAKE_CONFIGURATION_TYPES Asan)
    endif()
    if(NOT "Tsan" IN_LIST CMAKE_CONFIGURATION_TYPES)
        list(APPEND CMAKE_CONFIGURATION_TYPES Tsan)
    endif()
else()
    set(allowedBuildTypes Asan Tsan Debug Release RelWithDebInfo MinSizeRel)
    set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS "${allowedBuildTypes}")

    if(CMAKE_BUILD_TYPE AND NOT CMAKE_BUILD_TYPE IN_LIST allowedBuildTypes)
        message(FATAL_ERROR "Invalid build type: ${CMAKE_BUILD_TYPE}")
    endif()
endif()

# Asan
set(CMAKE_C_FLAGS_ASAN
    "${CMAKE_C_FLAGS_DEBUG} -fsanitize=address,leak,undefined -fno-omit-frame-pointer" CACHE STRING
    "Flags used by the C compiler for Asan build type or configuration." FORCE)

set(CMAKE_CXX_FLAGS_ASAN
    "${CMAKE_CXX_FLAGS_DEBUG} -fsanitize=address,leak,undefined -fno-omit-frame-pointer" CACHE STRING
    "Flags used by the C++ compiler for Asan build type or configuration." FORCE)

set(CMAKE_EXE_LINKER_FLAGS_ASAN
    "${CMAKE_EXE_LINKER_FLAGS_DEBUG} -fsanitize=address,leak,undefined" CACHE STRING
    "Linker flags to be used to create executables for Asan build type." FORCE)

set(CMAKE_SHARED_LINKER_FLAGS_ASAN
    "${CMAKE_SHARED_LINKER_FLAGS_DEBUG} -fsanitize=address,leak,undefined" CACHE STRING
    "Linker lags to be used to create shared libraries for Asan build type." FORCE)

# Tsan
set(CMAKE_C_FLAGS_TSAN
    "${CMAKE_C_FLAGS_DEBUG} -fsanitize=thread,undefined -fno-omit-frame-pointer" CACHE STRING
    "Flags used by the C compiler for Asan build type or configuration." FORCE)

set(CMAKE_CXX_FLAGS_TSAN
    "${CMAKE_CXX_FLAGS_DEBUG} -fsanitize=thread,undefined -fno-omit-frame-pointer" CACHE STRING
    "Flags used by the C++ compiler for Asan build type or configuration." FORCE)

set(CMAKE_EXE_LINKER_FLAGS_TSAN
    "${CMAKE_EXE_LINKER_FLAGS_DEBUG} -fsanitize=thread,undefined" CACHE STRING
    "Linker flags to be used to create executables for Tsan build type." FORCE)

set(CMAKE_SHARED_LINKER_FLAGS_TSAN
    "${CMAKE_SHARED_LINKER_FLAGS_DEBUG} -fsanitize=thread,undefined" CACHE STRING
    "Linker lags to be used to create shared libraries for Tsan build type." FORCE)
endif()


# Find Threads for C++ multithreading
set(CMAKE_THREAD_PREFER_PTHREAD TRUE)
set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads REQUIRED)

# Find libav* FFmpeg libraries using pkg-config
find_package(PkgConfig REQUIRED)
pkg_check_modules(LIBAV REQUIRED IMPORTED_TARGET
    libavdevice
    libavfilter
    libavformat
    libavcodec
    libswresample
    libswscale
    libavutil
)

# pdq library
add_subdirectory(pdq)

# vpdq library
add_subdirectory(vpdq)

# CLI programs
# TODO: Make this a custom command/option. This isn't necessary to just build the library.
add_subdirectory(apps)
