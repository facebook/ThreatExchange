# VPDQ library
# This will produce one library file: libvpdqlib

set(VPDQSOURCES
    cpp/hashing/bufferhasher.cpp
    cpp/hashing/filehasher.cpp
    cpp/hashing/ffmpegutils.cpp
    cpp/hashing/ffmpegwrapper.cpp
    cpp/hashing/hasher.cpp
    cpp/hashing/matchTwoHash.cpp
    cpp/io/vpdqio.cpp
)

set(VPDQHEADERS
    cpp/hashing/bufferhasher.h
    cpp/hashing/filehasher.h
    cpp/hashing/ffmpegutils.h
    cpp/hashing/ffmpegwrapper.h
    cpp/hashing/hasher.h
    cpp/hashing/vpdqHashType.h
    cpp/hashing/matchTwoHash.h
    cpp/io/vpdqio.h
)

# Make an automatic library - will be static or dynamic based on user setting.
# Note: Including header files here helps IDEs, but is not required.
add_library(vpdqlib ${VPDQSOURCES} ${VPDQHEADERS})

# We need this directory, and users of the library will need it too.
target_include_directories(vpdqlib PUBLIC
    # We go up a directory so that the source files can include the
    # whole path, e.g. <vpdq/cpp/hashing/vpdqHashType.h>
    ${CMAKE_CURRENT_SOURCE_DIR}/..
)

target_link_libraries(vpdqlib PUBLIC PkgConfig::LIBAV Threads::Threads pdqlib)

# All users of this library will need at least C++14
target_compile_features(vpdqlib PUBLIC cxx_std_14)

# Turn on -fPIC
set_target_properties(vpdqlib PROPERTIES POSITION_INDEPENDENT_CODE ON)

if(NOT MSVC)
    set(VPDQ_WARNING_FLAGS
        -Wall
        -Wextra
        -Wpedantic
        -Werror
        -Wno-error=deprecated-declarations # Avoid compile error if something gets deprecated. Warning will still show up.
    )
    target_compile_options(vpdqlib PRIVATE ${VPDQ_WARNING_FLAGS})
endif()
