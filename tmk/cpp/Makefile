# ----------------------------------------------------------------
CXX=g++ # please customize according to your system --- Note: Apple clang is not supported 
CC=$(CXX) -O2 -std=c++14 -I../.. #
FFMPEG=/usr/bin/ffmpeg # please customize according to your installation (but do not commit)

ifeq ($(OS),Windows_NT)
  CC_IF_WIN=$(CXX) -O2 -std=gnu++14 -I../..
  OMP_LIB=-lgomp
else
  CC_IF_WIN=$(CXX) -O2 -std=c++14 -I../.. 
  OMP_LIB=-lgomp
endif

# ----------------------------------------------------------------
LIBHDR= \
../../pdq/cpp/common/pdqbasetypes.h \
../../pdq/cpp/common/pdqhashtypes.h \
../../pdq/cpp/downscaling/downscaling.h \
../../pdq/cpp/hashing/pdqhashing.h \
../../pdq/cpp/hashing/torben.h \
./algo/tmkfv.h \
./hashing/bufferhashers.h \
./hashing/filehasher.h \
./io/tmkio.h \
./io/tmkiotypes.h \
./lib/vec.h \
./raster/rasterwriters.h \
./raster/timeresamplers.h

LIBSRC= \
../../pdq/cpp/downscaling/downscaling.cpp \
../../pdq/cpp/hashing/pdqhashing.cpp \
../../pdq/cpp/hashing/torben.cpp \
./lib/vec.cpp \
./algo/tmkfv.cpp \
./hashing/bufferhashers.cpp \
./hashing/filehasher.cpp \
./io/tmkio.cpp \
./raster/rasterwriters.cpp \
./raster/timeresamplers.cpp

LIBOBJ= \
../../pdq/cpp/downscaling/downscaling.o \
../../pdq/cpp/hashing/pdqhashing.o \
../../pdq/cpp/hashing/torben.o \
./lib/vec.o \
./algo/tmkfv.o \
./hashing/bufferhashers.o \
./hashing/filehasher.o \
./io/tmkio.o \
./raster/rasterwriters.o \
./raster/timeresamplers.o

EXE_PARALLEL= \
 tmk-query-parallel \
 tmk-clusterize-parallel \
 tmk-two-level-score-parallel \
 tmk-query-with-faiss

EXE= \
 tmk-hash-video \
 feat2tmk \
 vstr2feat \
 featdump \
 tmkdump \
 tmk-compare-two-tmks \
 tmk-show-pair-offsets \
 tmk-clusterize \
 tmk-query \
 tmk-two-level-score

# ================================================================
all: $(EXE) regtest

parallel: $(EXE_PARALLEL)

regtest: tmk-hash-video tmk-compare-two-tmks .always
	mkdir -p ./regtest
	./tmk-hash-video -f $(FFMPEG) -d ./regtest -i ../sample-videos/chair-19-sd-bar.mp4
	./tmk-hash-video -f $(FFMPEG) -d ./regtest -i ../sample-videos/chair-20-sd-bar.mp4
	./tmk-hash-video -f $(FFMPEG) -d ./regtest -i ../sample-videos/chair-22-sd-grey-bar.mp4
	./tmk-hash-video -f $(FFMPEG) -d ./regtest -i ../sample-videos/chair-22-sd-sepia-bar.mp4
	./tmk-hash-video -f $(FFMPEG) -d ./regtest -i ../sample-videos/chair-22-with-large-logo-bar.mp4
	./tmk-hash-video -f $(FFMPEG) -d ./regtest -i ../sample-videos/chair-22-with-small-logo-bar.mp4
	./tmk-hash-video -f $(FFMPEG) -d ./regtest -i ../sample-videos/chair-orig-22-fhd-no-bar.mp4
	./tmk-hash-video -f $(FFMPEG) -d ./regtest -i ../sample-videos/chair-orig-22-hd-no-bar.mp4
	./tmk-hash-video -f $(FFMPEG) -d ./regtest -i ../sample-videos/chair-orig-22-sd-bar.mp4
	./tmk-hash-video -f $(FFMPEG) -d ./regtest -i ../sample-videos/doorknob-hd-no-bar.mp4
	./tmk-hash-video -f $(FFMPEG) -d ./regtest -i ../sample-videos/pattern-hd-no-bar.mp4
	./tmk-hash-video -f $(FFMPEG) -d ./regtest -i ../sample-videos/pattern-longer-no-bar.mp4
	./tmk-hash-video -f $(FFMPEG) -d ./regtest -i ../sample-videos/pattern-sd-grey-bar.mp4
	./tmk-hash-video -f $(FFMPEG) -d ./regtest -i ../sample-videos/pattern-sd-with-large-logo-bar.mp4
	./tmk-hash-video -f $(FFMPEG) -d ./regtest -i ../sample-videos/pattern-sd-with-small-logo-bar.mp4
	@echo
	./tmk-compare-two-tmks ./regtest/chair-19-sd-bar.tmk                ../sample-hashes/chair-19-sd-bar.tmk
	./tmk-compare-two-tmks ./regtest/chair-20-sd-bar.tmk                ../sample-hashes/chair-20-sd-bar.tmk
	./tmk-compare-two-tmks ./regtest/chair-22-sd-grey-bar.tmk           ../sample-hashes/chair-22-sd-grey-bar.tmk
	./tmk-compare-two-tmks ./regtest/chair-22-sd-sepia-bar.tmk          ../sample-hashes/chair-22-sd-sepia-bar.tmk
	./tmk-compare-two-tmks ./regtest/chair-22-with-large-logo-bar.tmk   ../sample-hashes/chair-22-with-large-logo-bar.tmk
	./tmk-compare-two-tmks ./regtest/chair-22-with-small-logo-bar.tmk   ../sample-hashes/chair-22-with-small-logo-bar.tmk
	./tmk-compare-two-tmks ./regtest/chair-orig-22-fhd-no-bar.tmk       ../sample-hashes/chair-orig-22-fhd-no-bar.tmk
	./tmk-compare-two-tmks ./regtest/chair-orig-22-hd-no-bar.tmk        ../sample-hashes/chair-orig-22-hd-no-bar.tmk
	./tmk-compare-two-tmks ./regtest/chair-orig-22-sd-bar.tmk           ../sample-hashes/chair-orig-22-sd-bar.tmk
	./tmk-compare-two-tmks ./regtest/doorknob-hd-no-bar.tmk             ../sample-hashes/doorknob-hd-no-bar.tmk
	./tmk-compare-two-tmks ./regtest/pattern-hd-no-bar.tmk              ../sample-hashes/pattern-hd-no-bar.tmk
	./tmk-compare-two-tmks ./regtest/pattern-longer-no-bar.tmk          ../sample-hashes/pattern-longer-no-bar.tmk
	./tmk-compare-two-tmks ./regtest/pattern-sd-grey-bar.tmk            ../sample-hashes/pattern-sd-grey-bar.tmk
	./tmk-compare-two-tmks ./regtest/pattern-sd-with-large-logo-bar.tmk ../sample-hashes/pattern-sd-with-large-logo-bar.tmk
	./tmk-compare-two-tmks ./regtest/pattern-sd-with-small-logo-bar.tmk ../sample-hashes/pattern-sd-with-small-logo-bar.tmk
	@echo
	@echo REGRESSION PASSED

# ================================================================
libtmk.a: $(LIBOBJ)
	ar r libtmk.a $(LIBOBJ)

../../pdq/cpp/downscaling/downscaling.o: ../../pdq/cpp/downscaling/downscaling.cpp $(LIBHDR)
	$(CC) -c ../../pdq/cpp/downscaling/downscaling.cpp -o ../../pdq/cpp/downscaling/downscaling.o

../../pdq/cpp/hashing/pdqhashing.o: ../../pdq/cpp/hashing/pdqhashing.cpp $(LIBHDR)
	$(CC) -c ../../pdq/cpp/hashing/pdqhashing.cpp -o ../../pdq/cpp/hashing/pdqhashing.o

../../pdq/cpp/hashing/torben.o: ../../pdq/cpp/hashing/torben.cpp $(LIBHDR)
	$(CC) -c ../../pdq/cpp/hashing/torben.cpp -o ../../pdq/cpp/hashing/torben.o

./lib/vec.o: ./lib/vec.cpp $(LIBHDR)
	$(CC) -c ./lib/vec.cpp -o ./lib/vec.o

./algo/tmkfv.o: ./algo/tmkfv.cpp $(LIBHDR)
	$(CC) -c ./algo/tmkfv.cpp -o ./algo/tmkfv.o

./hashing/bufferhashers.o: ./hashing/bufferhashers.cpp $(LIBHDR)
	$(CC) -c ./hashing/bufferhashers.cpp -o ./hashing/bufferhashers.o

./hashing/filehasher.o: ./hashing/filehasher.cpp $(LIBHDR)
	$(CC_IF_WIN) -c ./hashing/filehasher.cpp -o ./hashing/filehasher.o

./io/tmkio.o: ./io/tmkio.cpp $(LIBHDR)
	$(CC) -c ./io/tmkio.cpp -o ./io/tmkio.o

./raster/rasterwriters.o: ./raster/rasterwriters.cpp $(LIBHDR)
	$(CC) -c ./raster/rasterwriters.cpp -o ./raster/rasterwriters.o

./raster/timeresamplers.o: ./raster/timeresamplers.cpp $(LIBHDR)
	$(CC) -c ./raster/timeresamplers.cpp -o ./raster/timeresamplers.o

# ================================================================
tmk-hash-video: ./bin/tmk-hash-video.cpp $(LIBHDR) libtmk.a
	$(CC) bin/tmk-hash-video.cpp -o tmk-hash-video -L. -ltmk

# ----------------------------------------------------------------
vstr2feat: ./bin/vstr2feat.cpp $(LIBHDR) libtmk.a
	$(CC) bin/vstr2feat.cpp -o vstr2feat -L. -ltmk
feat2tmk: ./bin/feat2tmk.cpp $(LIBHDR) libtmk.a
	$(CC) bin/feat2tmk.cpp -o feat2tmk -L. -ltmk
featdump: ./bin/featdump.cpp $(LIBHDR) libtmk.a
	$(CC) bin/featdump.cpp -o featdump -L. -ltmk
tmkdump: ./bin/tmkdump.cpp $(LIBHDR) libtmk.a
	$(CC_IF_WIN) bin/tmkdump.cpp -o tmkdump -L. -ltmk

# ----------------------------------------------------------------
tmk-compare-two-tmks: ./bin/tmk-compare-two-tmks.cpp $(LIBHDR) libtmk.a
	$(CC) bin/tmk-compare-two-tmks.cpp -o tmk-compare-two-tmks -L. -ltmk
tmk-show-pair-offsets: ./bin/tmk-show-pair-offsets.cpp $(LIBHDR) libtmk.a
	$(CC) bin/tmk-show-pair-offsets.cpp -o tmk-show-pair-offsets -L. -ltmk

# ----------------------------------------------------------------
tmk-clusterize: ./bin/tmk-clusterize.cpp $(LIBHDR) libtmk.a
	$(CC_IF_WIN) bin/tmk-clusterize.cpp -o tmk-clusterize -L. -ltmk
tmk-query: ./bin/tmk-query.cpp $(LIBHDR) libtmk.a
	$(CC_IF_WIN) bin/tmk-query.cpp -o tmk-query -L. -ltmk
tmk-two-level-score: ./bin/tmk-two-level-score.cpp $(LIBHDR) libtmk.a
	$(CC_IF_WIN) bin/tmk-two-level-score.cpp -o tmk-two-level-score -L. -ltmk

# ----------------------------------------------------------------
tmk-clusterize-parallel: ./bin/tmk-clusterize.cpp $(LIBHDR) libtmk.a
	$(CC_IF_WIN) -Xpreprocessor -fopenmp bin/tmk-clusterize.cpp -o tmk-clusterize-parallel -L. -ltmk $(OMP_LIB)
tmk-query-with-faiss: ./bin/tmk-query-with-faiss.cpp $(LIBHDR) libtmk.a
	$(CC_IF_WIN) -Xpreprocessor -fopenmp -I/usr/local/include/faiss bin/tmk-query-with-faiss.cpp -o tmk-query-with-faiss -L. -L/usr/local/lib -ltmk -lfaiss $(OMP_LIB) -Wl,-rpath,/usr/local/lib
tmk-query-parallel: ./bin/tmk-query.cpp $(LIBHDR) libtmk.a
	$(CC_IF_WIN) -Xpreprocessor -fopenmp bin/tmk-query.cpp -o tmk-query-parallel -L. -ltmk $(OMP_LIB)
tmk-two-level-score-parallel: ./bin/tmk-two-level-score.cpp $(LIBHDR) libtmk.a
	$(CC_IF_WIN) -Xpreprocessor -fopenmp bin/tmk-two-level-score.cpp -o tmk-two-level-score-parallel -L. -ltmk $(OMP_LIB)

format:
	find . -iname '*.h' -o -iname '*.cpp' | xargs clang-format -i
check-format:
	find . -iname '*.h' -o -iname '*.cpp' | xargs clang-format -n --Werror
# ================================================================
tags:
	ctags -R .

# ----------------------------------------------------------------
clean:
	-rm -vf tags
	-rm -vf libtmk.a
	-rm -vf $(LIBOBJ)
	-rm -vf $(EXE)
	-rm -vf $(EXE_PARALLEL)
	-rm -vf regtest/*.tmk

.always:
	@true
