// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

package pdqhashing.tools;

import pdqhashing.indexer.MIH256;
import pdqhashing.types.Hash256;
import pdqhashing.types.Hash256AndMetadata;
import pdqhashing.types.MIHDimensionExceededException;
import pdqhashing.utils.HashReaderUtil;

import java.io.PrintStream;
import java.util.Vector;

/**
 * Takes two files containing hashes with metadata: the 'needles' file and the
 * 'haystack' file, and looks up each of the former within the latter.  This is
 * an ops tool, as well as demo code for the PDQ reference implementation.
 *
 * See pdqhashing/utils/HashReaderUtil.java for file-format information.
 *
 * See also the usage function for usage information.
 */
public class MIHQueryTool {
  private static final String PROGNAME = "MIHQueryTool";
  private static final int DEFAULT_PDQ_DISTANCE_THRESHOLD = 32;

  // ----------------------------------------------------------------
  // Helper class for tracking image-to-image deltas
  private static class Context {
    public int numPDQHash;
    public Hash256 pdqHashPrev;
    public boolean hadError;
    public Context(int _numPDQHash, Hash256 _pdqHashPrev, boolean _hadError) {
      this.numPDQHash = _numPDQHash;
      this.pdqHashPrev = _pdqHashPrev;
      this.hadError = _hadError;
    }
  }

  // ----------------------------------------------------------------
  private static void usage(int rc) {
    PrintStream o = (rc == 0) ? System.out : System.err;
    o.printf("Usage: %s  [options] {needles file} {haystack file}\n", PROGNAME);
    o.printf("Files should have one hex-formatted 256-bit hash per line,\n");
    o.printf("optionally prefixed by \"hash=\". If a comma and other text\n");
    o.printf("follows the hash, it is used as metadata; else, a counter is\n");
    o.printf("used as the metadata.\n");
    o.printf("\n");
    o.printf("Options:\n");
    o.printf("-h|--help    Print this message.\n");
    o.printf("-d {n}       Distance threshold: default %d.\n",
      DEFAULT_PDQ_DISTANCE_THRESHOLD);
    o.printf("-u|--unified-output Print needle/haystack pairs on all match lines,.\n");
    o.printf("             rather than the default which is needle hashes then matches.\n");
    o.printf("-b|--brute-force-query Use linear search not MIH.\n");
    o.printf("-v|--invert Show needles not matching any in haystack.\n");
    System.exit(rc);
  }

  // ----------------------------------------------------------------
  public static void main(String[] args) {

    boolean doBruteForceQuery = false;
    int distanceThreshold = DEFAULT_PDQ_DISTANCE_THRESHOLD;
    boolean doUnifiedOutput = false;
    boolean doInvert = false;

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

      } else if (args[argi].equals("-u") || args[argi].equals("--unified-output")) {
        doUnifiedOutput = true;
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

      } else if (args[argi].equals("-v")) {
        doInvert = true;
        argi++;

      } else {
        usage(1);
      }
    }

    if ((argc - argi) != 2) {
      usage(1);
    }
    String needlesFilename = args[argi];
    String haystackFilename = args[argi+1];

    //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    long t1, t2;
    double duration; // in seconds

    //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    // Load hashes+metadata.

    Vector<Hash256AndMetadata<String>> needles = new Vector<Hash256AndMetadata<String>>();
    Vector<Hash256AndMetadata<String>> haystack = new Vector<Hash256AndMetadata<String>>();

    t1 = System.nanoTime();

    HashReaderUtil.loadHashesAndMetadataFromFileOrDie(PROGNAME, needlesFilename, needles);
    HashReaderUtil.loadHashesAndMetadataFromFileOrDie(PROGNAME, haystackFilename, haystack);

    t2 = System.nanoTime();
    duration = (t2 - t1) / 1e9;
    System.out.printf("read_seconds=%.3e\n", duration);

    //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    // Build the MIH data structure.

    t1 = System.nanoTime();

    MIH256<String> mih = new MIH256<String>();

    for (Hash256AndMetadata<String> pair : haystack) {
      mih.insert(pair.hash, pair.metadata);
    }

    t2 = System.nanoTime();
    duration = (t2 - t1) / 1e9;
    System.out.printf("build_seconds=%.3e\n", duration);

    //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    // Do the lookups.

    t1 = System.nanoTime();

    if (doInvert) {

      for (Hash256AndMetadata<String> needlePair : needles) {
        Hash256AndMetadata<String> matchPair = null;
        try {
          matchPair = doBruteForceQuery
            ? mih.bruteForceQueryAny(needlePair.hash, distanceThreshold)
            : mih.queryAny(needlePair.hash, distanceThreshold);
        } catch (MIHDimensionExceededException e) {
          System.err.printf("%s: %s\n", PROGNAME, e.getErrorMessage());
          System.exit(1);
        }

        if (matchPair == null) {
          System.out.printf("hash=%s,%s\n",
            needlePair.hash.toString(), needlePair.metadata);
        }
      }

    } else if (doUnifiedOutput) {
      Vector<Hash256AndMetadata<String>> matches = new Vector<Hash256AndMetadata<String>>();

      for (Hash256AndMetadata<String> needlePair : needles) {

        matches.clear();

        try {
          if (doBruteForceQuery) {
            mih.bruteForceQueryAll(needlePair.hash, distanceThreshold, matches);
          } else {
            mih.queryAll(needlePair.hash, distanceThreshold, matches);
          }
        } catch (MIHDimensionExceededException e) {
          System.err.printf("%s: %s\n", PROGNAME, e.getErrorMessage());
          System.exit(1);
        }

        if (matches.isEmpty()) {
          System.out.printf("needle=%s,%s,matches=none\n", needlePair.hash.toString(), needlePair.metadata);
        } else {
          for (Hash256AndMetadata<String> matchPair : matches) {
            System.out.printf("d=%d,needle=%s,%s,match=%s,%s\n",
              matchPair.hash.hammingDistance(needlePair.hash),
              needlePair.hash.toString(),
              needlePair.metadata,
              matchPair.hash.toString(),
              matchPair.metadata);
          }
        }
      }

    } else {

      Vector<Hash256AndMetadata<String>> matches = new Vector<Hash256AndMetadata<String>>();

      boolean first = true;
      for (Hash256AndMetadata<String> needlePair : needles) {
        if (!first) {
          System.out.printf("\n");
        }
        first = false;
        System.out.printf("needle=%s\n", needlePair.hash.toString());

        matches.clear();

        try {
          if (doBruteForceQuery) {
            mih.bruteForceQueryAll(needlePair.hash, distanceThreshold, matches);
          } else {
            mih.queryAll(needlePair.hash, distanceThreshold, matches);
          }
        } catch (MIHDimensionExceededException e) {
          System.err.printf("%s: %s\n", PROGNAME, e.getErrorMessage());
          System.exit(1);
        }

        for (Hash256AndMetadata<String> matchPair : matches) {
          System.out.printf("d=%d,match=%s,%s\n",
            matchPair.hash.hammingDistance(needlePair.hash),
            matchPair.hash.toString(),
            matchPair.metadata);
        }
      }

    }

    t2 = System.nanoTime();
    duration = (t2 - t1) / 1e9;
    System.out.printf("query_seconds=%.3e\n", duration);

  }
}
