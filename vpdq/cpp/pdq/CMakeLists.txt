# PDQ library
# This will produce one library file: libpdqlib

set(PDQSOURCES
    cpp/common/pdqhashtypes.cpp
    cpp/hashing/pdqhashing.cpp
    cpp/common/pdqhamming.cpp
    cpp/io/hashio.cpp
    cpp/downscaling/downscaling.cpp
    cpp/hashing/torben.cpp
)

set(PDQHEADERS
    cpp/common/pdqhashtypes.h
    cpp/common/pdqbasetypes.h
    cpp/common/pdqhamming.h
    cpp/hashing/pdqhashing.h
    cpp/io/hashio.h
    cpp/downscaling/downscaling.h
    cpp/hashing/torben.h
)

# Note: Including header files here helps IDEs, but is not required.
add_library(pdqlib ${PDQHEADERS} ${PDQSOURCES})

# We need this directory, and users of the library will need it too.
target_include_directories(pdqlib PUBLIC
    # We go up a directory so that the source files can include the
    # whole path, e.g. <pdq/cpp/common/pdqbasetypes.h>
    ${CMAKE_CURRENT_SOURCE_DIR}/..
)

# Turn on -fPIC
set_target_properties(pdqlib PROPERTIES POSITION_INDEPENDENT_CODE ON)

# All users of this library will need at least C++11
target_compile_features(pdqlib PUBLIC cxx_std_11)
