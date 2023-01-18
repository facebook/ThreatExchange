// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

package pdqhashing.tools;

import pdqhashing.indexer.MIH256;
import pdqhashing.types.Hash256;
import pdqhashing.types.Hash256AndMetadata;
import pdqhashing.types.MIHDimensionExceededException;
import pdqhashing.types.PDQHashFormatException;
import pdqhashing.utils.HashReaderUtil;

import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintStream;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.Vector;

/**
 * Takes hashes with metadata and clusters them among one another.  This is an
 * ops tool, as well as demo code for the PDQ reference implementation.
 *
 * NOTE: There are clusterize256 and clusterize256x.
 *
 * * The former ingests all hashes in memory. It produces cluster sizes as
 *   output. It's slower and is nice for one-stop shopping on a few thousand
 *   hashes.
 *
 * * The latter is streaming, uses less memory, and is far faster. It does not
 *   produce cluster sizes on output. (Those need to be computed as an
 *   afterpass.) It necessary for operating on millions of hashes.
 *
 *
 * A 'greedy' clusterer is used: given first-encountered hash h1, all subsequent
 * hashes within the specified distance threshold of h1 are listed within that
 * cluster. Another hash, call it h2, even if just outside h1's radius will be
 * put in another cluster. Any hashes in the 'overlap' (within threshold of h1
 * and h2) will *only* be listed in h1's clsuter, not h2's. This means if there
 * are N hashes as input, this program lists N hashes as output.
 *
 * See pdqhashing/utils/HashReaderUtil.java for file-format information.
 *
 * See the usage function for more usage information.
 * ================================================================
 */

public class Clusterize256xTool {
  private static final String PROGNAME = "Clusterize256xTool";
  private static final int DEFAULT_PDQ_DISTANCE_THRESHOLD = 31;

  // ----------------------------------------------------------------
  private static void usage(int rc) {
    PrintStream o = (rc == 0) ? System.out : System.err;
    o.printf("Usage: %s  [options] {zero or more hash-files}\n", PROGNAME);
    o.printf("If zero filenames are provided, stdin is read.\n");
    o.printf("Files should have one hex-formatted 256-bit hash per line,\n");
    o.printf("optionally prefixed by \"hash=\". If a comma and other text\n");
    o.printf("follows the hash, it is used as metadata; else, a counter is\n");
    o.printf("used as the metadata.\n");
    o.printf("\n");
    o.printf("Options:\n");
    o.printf("-h|--help    Print this message.\n");
    o.printf("-b|--brute-force-query Use linear search not MIH.\n");
    o.printf("-d {n}       Distance threshold: default %d.\n",
      DEFAULT_PDQ_DISTANCE_THRESHOLD);
    o.printf("--trace {n}  Print to stderr every n items. Default off.\n");
    System.exit(rc);
  }

  // ----------------------------------------------------------------
  public static void main(String[] args) {
    boolean doBruteForceQuery = false;
    int  distanceThreshold = DEFAULT_PDQ_DISTANCE_THRESHOLD;
    int  traceCount = 0;

    // Parse command-line flags. I'm explicitly not using gflags or other such
    // libraries, to minimize the number of external dependencies for this
    // project.
    int argi = 0;
    int argc = args.length;
    while (argi < argc) {
      if (!args[argi].startsWith("-")) {
        break;
      }

      if (args[argi].equals("-h") || args[argi].equals("--help")) {
        usage(0);
      } else if (args[argi].equals("-b") || args[argi].equals("--brute-force-query")) {
        doBruteForceQuery = true;
        argi++;

      } else if (args[argi].equals("-d")) {
        if ((argc - argi) < 2)
          usage(1);
        try {
          distanceThreshold = Integer.parseInt(args[argi+1]);
        } catch (NumberFormatException e) {
          usage(1);
        }
        argi += 2;

      } else if (args[argi].equals("--trace")) {
        if ((argc - argi) < 2)
          usage(1);
        try {
          traceCount = Integer.parseInt(args[argi+1]);
        } catch (NumberFormatException e) {
          usage(1);
        }
        argi += 2;

      } else {
        usage(1);
      }
    }
    args = Arrays.copyOfRange(args, argi, argc);

    //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    MIH256<String> mihWithCenters = new MIH256<String>();
    Map<Hash256,Integer> centersToIndices = new HashMap<Hash256,Integer>();

    int lineCounter = 0;
    if (args.length == 0) {
      BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
      handleStream(reader, "(standard input)", mihWithCenters, centersToIndices, distanceThreshold,
        lineCounter, traceCount, doBruteForceQuery);
    } else {
      for (String filename : args) {
        BufferedReader reader = null;
        try {
          reader = new BufferedReader(new FileReader(filename));
        } catch (FileNotFoundException e) {
          System.err.printf("%s: could not open \"%s\" for read.\n", PROGNAME, filename);
          System.exit(1);
        }
        lineCounter = handleStream(reader, filename, mihWithCenters, centersToIndices, distanceThreshold,
          lineCounter, traceCount, doBruteForceQuery);
        try {
          reader.close();
        } catch (IOException e) {
          System.err.printf("%s: could not close \"%s\" after read.\n", PROGNAME, filename);
          System.exit(1);
        }
      }
    }
  }

  // ----------------------------------------------------------------
  private static int handleStream( // returns line-counter
    BufferedReader reader,
    String filename,
    MIH256<String> mihWithCenters,
    Map<Hash256,Integer> centersToIndices,
    int distanceThreshold,
    int lineCounter,
    int traceCount,
    boolean doBruteForceQuery
  ) {

    while (true) {
      Hash256AndMetadata<String> inputPair = null;
      try {
        inputPair = HashReaderUtil.loadHashAndMetadataFromStream(reader, lineCounter);
      } catch (IOException e) {
        System.err.printf("%s: could not read line %d of file \"%s\".\n",
          PROGNAME, lineCounter, filename);
        System.exit(1);
      } catch (PDQHashFormatException e) {
        System.err.printf("%s: unparseable hash \"%s\" at line %d of file \"%s\".\n",
          PROGNAME, e.getUnacceptableInput(), lineCounter+1, filename);
        System.exit(1);
      }
      if (inputPair == null) {
        break;
      }
      if (traceCount > 0) {
        if ((lineCounter % traceCount) == 0) {
          System.err.printf("-- %d\n", lineCounter);
        }
      }
      lineCounter++;

      Vector<Hash256AndMetadata<String>> matches = new Vector<Hash256AndMetadata<String>>();
      Hash256AndMetadata<String> centerPair = null;
      try {
        centerPair = doBruteForceQuery
          ? mihWithCenters.bruteForceQueryAny(inputPair.hash, distanceThreshold)
          : mihWithCenters.queryAny(inputPair.hash, distanceThreshold);
      } catch (MIHDimensionExceededException e) {
        System.err.printf("%s: %s\n", PROGNAME, e.getErrorMessage());
        System.exit(1);
      }

      boolean isCenter = false;
      int matchClusterIndex = -1;
      if (centerPair == null) {
        isCenter = true;
        int insertionClusterIndex = mihWithCenters.size();
        mihWithCenters.insert(inputPair.hash, inputPair.metadata);
        centersToIndices.put(inputPair.hash, insertionClusterIndex);
        matchClusterIndex = insertionClusterIndex;
        centerPair = inputPair;
      } else {
        matchClusterIndex = centersToIndices.get(centerPair.hash);
      }

      System.out.printf("clidx=%d,hash1=%s,hash2=%s,is_center=%d,d=%d,%s\n",
        matchClusterIndex,
        inputPair.hash.toString(),
        centerPair.hash.toString(),
        isCenter ? 1 : 0,
        centerPair.hash.hammingDistance(inputPair.hash),
        inputPair.metadata);

    }
    return lineCounter;
  }
}
