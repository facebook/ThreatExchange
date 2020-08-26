# ================================================================
CLASSES=\
  src/main/java/pdqhashing/types/PDQHashFormatException.class \
  src/main/java/pdqhashing/types/Hash256.class \
  src/main/java/pdqhashing/types/Hash256AndMetadata.class \
  src/main/java/pdqhashing/types/HashAndQuality.class \
	src/main/java/pdqhashing/types/HashInt64.class \
  src/main/java/pdqhashing/types/MIHDimensionExceededException.class \
  src/main/java/pdqhashing/utils/MatrixUtil.class \
  src/main/java/pdqhashing/hasher/PDQHasher.class \
  src/main/java/pdqhashing/indexer/MIH256.class \
  src/main/java/pdqhashing/utils/HashReaderUtil.class \
  src/main/java/pdqhashing/tools/PDQPhotoHasherTool.class \
  src/main/java/pdqhashing/tools/Hash256Tool.class \
  src/main/java/pdqhashing/tools/MIHQueryTool.class \
  src/main/java/pdqhashing/tools/Clusterize256Tool.class \
  src/main/java/pdqhashing/tools/Clusterize256xTool.class

PDQJAR=pdq.jar

# ================================================================
top: jar run-reg-test

run-reg-test: .always
	./reg_test/run
itso:
	cp output-regtest/out reg_test/expected

# ================================================================
src/main/java/pdqhashing/types/Hash256.class: src/main/java/pdqhashing/types/Hash256.java
	javac -cp src/main/java src/main/java/pdqhashing/types/Hash256.java
src/main/java/pdqhashing/types/Hash256AndMetadata.class: src/main/java/pdqhashing/types/Hash256AndMetadata.java
	javac -cp src/main/java src/main/java/pdqhashing/types/Hash256AndMetadata.java
src/main/java/pdqhashing/types/HashAndQuality.class: src/main/java/pdqhashing/types/HashAndQuality.java
	javac -cp src/main/java src/main/java/pdqhashing/types/HashAndQuality.java
src/main/java/pdqhashing/types/HashInt64.class: src/main/java/pdqhashing/types/HashInt64.java
	javac -cp src/main/java src/main/java/pdqhashing/types/HashInt64.java
src/main/java/pdqhashing/types/PDQHashFormatException.class: src/main/java/pdqhashing/types/PDQHashFormatException.java
	javac -cp src/main/java src/main/java/pdqhashing/types/PDQHashFormatException.java
src/main/java/pdqhashing/types/MIHDimensionExceededException.class: src/main/java/pdqhashing/types/MIHDimensionExceededException.java
	javac -cp src/main/java src/main/java/pdqhashing/types/MIHDimensionExceededException.java
src/main/java/pdqhashing/utils/MatrixUtil.class: src/main/java/pdqhashing/utils/MatrixUtil.java
	javac -cp src/main/java src/main/java/pdqhashing/utils/MatrixUtil.java
src/main/java/pdqhashing/hasher/PDQHasher.class: src/main/java/pdqhashing/hasher/PDQHasher.java
	javac -cp src/main/java src/main/java/pdqhashing/hasher/PDQHasher.java
src/main/java/pdqhashing/indexer/MIH256.class: src/main/java/pdqhashing/indexer/MIH256.java
	javac -cp src/main/java src/main/java/pdqhashing/indexer/MIH256.java
src/main/java/pdqhashing/utils/HashReaderUtil.class: src/main/java/pdqhashing/utils/HashReaderUtil.java
	javac -cp src/main/java src/main/java/pdqhashing/utils/HashReaderUtil.java
src/main/java/pdqhashing/tools/PDQPhotoHasherTool.class: src/main/java/pdqhashing/tools/PDQPhotoHasherTool.java
	javac -cp src/main/java src/main/java/pdqhashing/tools/PDQPhotoHasherTool.java
src/main/java/pdqhashing/tools/Hash256Tool.class: src/main/java/pdqhashing/tools/Hash256Tool.java
	javac -cp src/main/java src/main/java/pdqhashing/tools/Hash256Tool.java
src/main/java/pdqhashing/tools/MIHQueryTool.class: src/main/java/pdqhashing/tools/MIHQueryTool.java
	javac -cp src/main/java src/main/java/pdqhashing/tools/MIHQueryTool.java
src/main/java/pdqhashing/tools/Clusterize256Tool.class: src/main/java/pdqhashing/tools/Clusterize256Tool.java
	javac -cp src/main/java src/main/java/pdqhashing/tools/Clusterize256Tool.java
src/main/java/pdqhashing/tools/Clusterize256xTool.class: src/main/java/pdqhashing/tools/Clusterize256xTool.java
	javac -cp src/main/java src/main/java/pdqhashing/tools/Clusterize256xTool.java

jar: $(CLASSES)
	cd src/main/java && jar cf $(PDQJAR) `find . -name '*.class'`
	mv src/main/java/$(PDQJAR) .

# ================================================================
tags: .always
	ctags -R .
clean:
	-rm -f $(CLASSES)
	-rm -f $(PDQJER)
cleantags:
	-rm -f tags
.always:
	@/usr/bin/true
