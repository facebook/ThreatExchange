# ================================================================
ifneq ($(findstring wasm, $(MAKECMDGOALS)), wasm)
CXX=g++ # please customize according to your system --- Note: Apple clang on M1 is not currently supported 
CC=$(CXX) -g -std=c++11
WFLAGS=-Wall -Wno-char-subscripts -Wno-stringop-truncation -Wno-class-memaccess -Wno-misleading-indentation -Wno-unknown-warning-option -Werror
LFLAGS=-lm -lpthread
else
CC=emcc -g -std=c++11 -D BUILD_WASM -s ERROR_ON_UNDEFINED_SYMBOLS=0 -s EXPORTED_RUNTIME_METHODS=['ccall','UTF8ToString ']  -s  EXPORTED_FUNCTIONS=['_getHash'] -s FORCE_FILESYSTEM=1 -s LLD_REPORT_UNDEFINED -s ERROR_ON_UNDEFINED_SYMBOLS=0 -s DISABLE_EXCEPTION_CATCHING=0 -s ALLOW_MEMORY_GROWTH=1
WFLAGS=-Wall -Wno-char-subscripts -Werror
LFLAGS=-lm
endif

IFLAGS=-I../.. -I.
# -Wno-char-subscripts -Wno-stringop-truncation -Wno-class-memaccess -Wno-misleading-indentation is because of CImg.h
WFLAGS=-Wall -Wno-char-subscripts -Wno-stringop-truncation -Wno-class-memaccess -Wno-misleading-indentation -Wno-unknown-warning-option -Werror
LFLAGS=-lm -lpthread

CCOPT=$(CC) $(CFLAGS) $(IFLAGS) $(WFLAGS) -O3
CCDBG=$(CC) -g $(CFLAGS) $(IFLAGS) $(WFLAGS)
CCSAN=clang -fsanitize=address -g $(CFLAGS) $(IFLAGS) $(WFLAGS)

# ================================================================
# Please replace CImg.h with your own system image-decoder and edit
# io/pdqio.cpp.
LIBHDRS=\
 common/pdqbasetypes.h \
 common/pdqhashtypes.h \
 io/hashio.h \
 common/pdqhamming.h \
 hashing/pdqhashing.h \
 downscaling/downscaling.h \
 io/pdqio.h \
 index/mih.h \
 hashing/torben.h \
 ./CImg.h \
 common/pdqutils.h

LIBSRCS=\
 common/pdqhashtypes.cpp \
 io/hashio.cpp \
 common/pdqhamming.cpp \
 hashing/pdqhashing.cpp \
 downscaling/downscaling.cpp \
 io/pdqio.cpp \
 hashing/torben.cpp \
 common/pdqutils.cpp

MAINS=\
 pdq-photo-hasher \
 test-mih \
 clusterize256 \
 snowball-clusterize256 \
 clusterize256x \
 mih-query \
 hashtool256 \
 pdq-downsample-demo \
 test-bits \
 hamming-tabulate \
 test-hamming \
 benchmark-query \
 benchmark-photo-hasher

WASMMAINS=pdq-photo-hasher

TESTS=\
 run-test-bits run-test-hamming run-reg-test

# ================================================================
top: $(MAINS) $(TESTS)

wasm: 
	$(CCOPT) bin/pdq-photo-hasher.cpp $(LIBSRCS) -o pdq-photo-hasher.js $(LFLAGS)
	@echo "All completed"

run-test-bits: test-bits
	./test-bits
run-test-hamming: test-hamming
	./test-hamming
run-reg-test:
	./reg_test/run
itso:
	cp output-regtest/out reg_test/expected

# ================================================================
hashtool256: bin/hashtool256.cpp $(LIBSRCS) $(LIBHDRS)
	$(CCOPT) bin/hashtool256.cpp $(LIBSRCS) -o hashtool256 $(LFLAGS)

test-bits: bin/test-bits.cpp $(LIBSRCS) $(LIBHDRS)
	$(CCOPT) bin/test-bits.cpp $(LIBSRCS) -o test-bits $(LFLAGS)

hamming-tabulate: bin/hamming-tabulate.cpp $(LIBSRCS) $(LIBHDRS)
	$(CCOPT) bin/hamming-tabulate.cpp $(LIBSRCS) -o test-hamming $(LFLAGS)

test-hamming: bin/test-hamming.cpp $(LIBSRCS) $(LIBHDRS)
	$(CCOPT) bin/test-hamming.cpp $(LIBSRCS) -o test-hamming $(LFLAGS)

pdq-photo-hasher: bin/pdq-photo-hasher.cpp $(LIBSRCS) $(LIBHDRS)
	$(CCOPT) bin/pdq-photo-hasher.cpp $(LIBSRCS) -o pdq-photo-hasher $(LFLAGS)

# Profile version. Usage:
# * make pdq-photo-hasher-prof
# * pdq-photo-hasher-prof {arguments>
# * gprof pdq-photo-hasher-prof gmon.out > myfile.txt
# Note: this profiler command works on Linux; not on OSX.
pdq-photo-hasher-prof: bin/pdq-photo-hasher.cpp $(LIBSRCS) $(LIBHDRS)
	$(CCDBG) -pg bin/pdq-photo-hasher.cpp $(LIBSRCS) -o pdq-photo-hasher-prof $(LFLAGS) -lpthread

pdqtestg: bin/pdq-photo-hasher.cpp $(LIBSRCS) $(LIBHDRS)
	$(CCDBG) bin/pdq-photo-hasher.cpp $(LIBSRCS) -o pdqtestg $(LFLAGS)
pdqtestsan: bin/pdq-photo-hasher.cpp $(LIBSRCS) $(LIBHDRS)
	$(CCSAN) bin/pdq-photo-hasher.cpp $(LIBSRCS) -o pdqtestsan $(LFLAGS)

pdq-downsample-demo: bin/pdq-downsample-demo.cpp $(LIBSRCS) $(LIBHDRS)
	$(CCOPT) bin/pdq-downsample-demo.cpp $(LIBSRCS) -o pdq-downsample-demo $(LFLAGS)

test-mih: bin/test-mih.cpp $(LIBSRCS) $(LIBHDRS)
	$(CCOPT) bin/test-mih.cpp $(LIBSRCS) -o test-mih $(LFLAGS)
test-mihg: bin/test-mih.cpp $(LIBSRCS) $(LIBHDRS)
	$(CCDBG) bin/test-mih.cpp $(LIBSRCS) -o test-mihg $(LFLAGS)
clusterize256: bin/clusterize256.cpp $(LIBSRCS) $(LIBHDRS)
	$(CCOPT) bin/clusterize256.cpp $(LIBSRCS) -o clusterize256 $(LFLAGS)
clusterize256-prof: bin/clusterize256.cpp $(LIBSRCS) $(LIBHDRS)
	$(CCDBG) -pg bin/clusterize256.cpp $(LIBSRCS) -o clusterize256-prof $(LFLAGS) -lpthread
snowball-clusterize256: bin/snowball-clusterize256.cpp $(LIBSRCS) $(LIBHDRS)
	$(CCOPT) bin/snowball-clusterize256.cpp $(LIBSRCS) -o snowball-clusterize256 $(LFLAGS)
clusterize256x: bin/clusterize256x.cpp $(LIBSRCS) $(LIBHDRS)
	$(CCOPT) bin/clusterize256x.cpp $(LIBSRCS) -o clusterize256x $(LFLAGS)
clusterize256x-prof: bin/clusterize256x.cpp $(LIBSRCS) $(LIBHDRS)
	$(CCDBG) -pg bin/clusterize256x.cpp $(LIBSRCS) -o clusterize256x-prof $(LFLAGS) -lpthread
mih-query: bin/mih-query.cpp $(LIBSRCS) $(LIBHDRS)
	$(CCOPT) bin/mih-query.cpp $(LIBSRCS) -o mih-query $(LFLAGS)

benchmark-query: bin/benchmark-query.cpp $(LIBSRCS) $(LIBHDRS)
	$(CCOPT) bin/benchmark-query.cpp $(LIBSRCS) -o benchmark-query $(LFLAGS)
benchmark-photo-hasher: bin/benchmark-photo-hasher.cpp $(LIBSRCS) $(LIBHDRS)
	$(CCOPT) bin/benchmark-photo-hasher.cpp $(LIBSRCS) -o benchmark-photo-hasher $(LFLAGS)

# Profile version. Usage:
# * make pdq-photo-hasher-prof
# * pdq-photo-hasher-prof {arguments>
# * gprof pdq-photo-hasher-prof gmon.out > myfile.txt
# Note: works on Linux; not on OSX.
test-mih-prof: bin/test-mih.cpp $(LIBSRCS) $(LIBHDRS)
	$(CCDBG) -pg bin/test-mih.cpp $(LIBSRCS) -o test-mih-prof $(LFLAGS) -lpthread

format:
	find . -iname '*.h' -o -iname '*.cpp' | xargs clang-format -i
check-format:
	find . -iname '*.h' -o -iname '*.cpp' | xargs clang-format -n --Werror

# ================================================================
tags: .always
	ctags -R .
clean:
	@-rm -vf $(MAINS) tags
	@-rm -rvf *.dSYM
.always:
	/usr/bin/true
