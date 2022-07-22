# ================================================================
CC=g++ -fPIC -O2 -std=c++14 -I../..




LIBHDR=\
../../pdq/cpp/common/pdqbasetypes.h \
../../pdq/cpp/common/pdqhashtypes.h \
../../pdq/cpp/hashing/pdqhashing.h \
../../pdq/cpp/io/hashio.h \
../../pdq/cpp/downscaling/downscaling.h \
../../pdq/cpp/hashing/torben.h \
./hashing/filehasher.h \
./hashing/bufferhasher.h \


LIBOBJ= \
../../pdq/cpp/common/pdqhashtypes.o \
../../pdq/cpp/hashing/pdqhashing.o \
../../pdq/cpp/io/hashio.o \
../../pdq/cpp/downscaling/downscaling.o \
../../pdq/cpp/hashing/torben.o \
./hashing/filehasher.o \
./hashing/bufferhasher.o \


# ================================================================
libvpdq.a: $(LIBOBJ)
	ar r libvpdq.a $(LIBOBJ)

../../pdq/cpp/hashing/pdqhashing.o: ../../pdq/cpp/hashing/pdqhashing.cpp $(LIBHDR)
	$(CC) -c ../../pdq/cpp/hashing/pdqhashing.cpp -o ../../pdq/cpp/hashing/pdqhashing.o

../../pdq/cpp/common/pdqhashtypes.o: ../../pdq/cpp/common/pdqhashtypes.cpp $(LIBHDR)
	$(CC) -c ../../pdq/cpp/common/pdqhashtypes.cpp -o ../../pdq/cpp/common/pdqhashtypes.o

../../pdq/cpp/io/hashio.o: ../../pdq/cpp/io/hashio.cpp $(LIBHDR)
	$(CC) -c ../../pdq/cpp/io/hashio.cpp -o ../../pdq/cpp/io/hashio.o

../../pdq/cpp/downscaling/downscaling.o: ../../pdq/cpp/downscaling/downscaling.cpp $(LIBHDR)
	$(CC) -c ../../pdq/cpp/downscaling/downscaling.cpp -o ../../pdq/cpp/downscaling/downscaling.o

../../pdq/cpp/hashing/torben.o: ../../pdq/cpp/hashing/torben.cpp $(LIBHDR)
	$(CC) -c ../../pdq/cpp/hashing/torben.cpp -o ../../pdq/cpp/hashing/torben.o

./hashing/bufferhasher.o: ./hashing/bufferhasher.cpp $(LIBHDR)
	$(CC) -c ./hashing/bufferhasher.cpp -o ./hashing/bufferhasher.o

./hashing/filehasher.o: ./hashing/filehasher.cpp $(LIBHDR)
	$(CC) -c ./hashing/filehasher.cpp -o ./hashing/filehasher.o

# ================================================================
all: libvpdq.a
