cmake_minimum_required(VERSION 3.17)

project(VPDQ CXX)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_FLAGS "-O2 -fPIC -Wall -Wextra -Werror -Wno-unused-function -Wno-deprecated-declarations")

# Enable threads
set(CMAKE_THREAD_PREFER_PTHREAD TRUE)
set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads REQUIRED)

# Find libav* FFmpeg libraries
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


set (PDQSOURCES
    pdq/cpp/common/pdqhashtypes.cpp
    pdq/cpp/hashing/pdqhashing.cpp
    pdq/cpp/common/pdqhamming.cpp
    pdq/cpp/io/hashio.cpp
    pdq/cpp/downscaling/downscaling.cpp
    pdq/cpp/hashing/torben.cpp
)

set (PDQHEADERS
    pdq/cpp/common/pdqhashtypes.h
    pdq/cpp/common/pdqbasetypes.h
    pdq/cpp/common/pdqhamming.h
    pdq/cpp/hashing/pdqhashing.h
    pdq/cpp/io/hashio.h
    pdq/cpp/downscaling/downscaling.h
    pdq/cpp/hashing/torben.h
)

set(SOURCES
    vpdq/cpp/hashing/bufferhasher.cpp
    vpdq/cpp/hashing/filehasher.cpp
    vpdq/cpp/hashing/ffmpegutils.cpp
    vpdq/cpp/hashing/ffmpegwrapper.cpp
    vpdq/cpp/hashing/hasher.cpp
    vpdq/cpp/hashing/matchTwoHash.cpp
    vpdq/cpp/io/vpdqio.cpp
)

SET(HEADERS
    vpdq/cpp/hashing/bufferhasher.h
    vpdq/cpp/hashing/filehasher.h
    vpdq/cpp/hashing/ffmpegutils.h
    vpdq/cpp/hashing/ffmpegwrapper.h
    vpdq/cpp/hashing/hasher.h
    vpdq/cpp/hashing/vpdqHashType.h
    vpdq/cpp/hashing/matchTwoHash.h
    vpdq/cpp/io/vpdqio.h
)

include_directories( vpdq/cpp/bin vpdq/cpp/hashing vpdq/cpp/io ${CMAKE_SOURCE_DIR} )

add_library(vpdq
    ${SOURCES}
    ${HEADERS}
    ${PDQSOURCES}
    ${PDQHEADERS}
)

target_include_directories(vpdq PRIVATE ${CMAKE_SOURCE_DIR})

add_executable(match-hashes-byline
    vpdq/cpp/bin/match-hashes-byline.cpp
)

add_executable(match-hashes-brute
    vpdq/cpp/bin/match-hashes-brute.cpp
)

add_executable(vpdq-hash-video
    vpdq/cpp/bin/vpdq-hash-video.cpp
)


target_link_libraries(vpdq
    PkgConfig::LIBAV
    Threads::Threads
)

target_link_libraries(match-hashes-byline
    vpdq
    PkgConfig::LIBAV
    Threads::Threads
)

target_link_libraries(match-hashes-brute
    vpdq
    PkgConfig::LIBAV
    Threads::Threads
)

target_link_libraries(vpdq-hash-video
    vpdq
    PkgConfig::LIBAV
    Threads::Threads
)

# Write the library dirs to a new-line delimited file for Cython to be able to locate LIBAV files
string(REPLACE ";" "\n" LIBRARY_DIRS "${LIBAV_STATIC_LIBRARY_DIRS}")
set(LIBRARY_DIRS_FILE "libraries-dirs.txt")
file(WRITE ${LIBRARY_DIRS_FILE} "${LIBRARY_DIRS}")
