# vpdq CLI programs

add_executable(match-hashes-brute match-hashes-brute.cpp)
add_executable(match-hashes-byline match-hashes-byline.cpp)
add_executable(vpdq-hash-video vpdq-hash-video.cpp)

target_link_libraries(match-hashes-brute PRIVATE vpdqlib)
target_link_libraries(match-hashes-byline PRIVATE vpdqlib)
target_link_libraries(vpdq-hash-video PRIVATE vpdqlib)
