// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

package pdqhashing.tools;

import pdqhashing.types.Hash256;
import pdqhashing.types.Hash256AndMetadata;
import pdqhashing.types.HashInt64;
import pdqhashing.types.PDQHashFormatException;
import pdqhashing.utils.HashReaderUtil;

import java.io.IOException;
import java.io.PrintStream;
import java.util.Arrays;
import java.util.Vector;

/**
 * This is an ops tool for doing various things to 256-bit hashes
 * with Hamming-distance metric.
 *
 * Input is 256-bit hex-formatted hashes, one per line.
 *
 * Please see the usage function for more information.
 */

public class Hash256Tool {
  private static String PROGNAME = "Hash256Tool";

  // ----------------------------------------------------------------
  private static void usage(int rc) {
    PrintStream o = (rc == 0) ? System.out : System.err;
    o.printf("Usage: %s {verb} [zero or more hash-files]\n", PROGNAME);
    o.printf("Hashes should be in hexadecimal format without leading 0x.\n");
    o.printf("If zero filenames are given on the command line, hashes are read from stdin.\n");
    o.printf("Norms and distances are computed using Hamming distance.\n");
    o.printf("Verbs:\n");
    o.printf(" norms:               Show hamming norms of hashes.\n");
    o.printf(" slotnorms:           Show slotwise (16-bit) hamming norms of hashes.\n");
    o.printf(" deltas:              Print hamming distances between adjacent hashes.\n");
    o.printf(" axors:               Print XORs of adjacent hashes.\n");
    o.printf(" fxors:               Print XORs of each hash with respect to the first.\n");
    o.printf(" matrix:              Print matrix of pairwise hamming distances.\n");
    o.printf(" cij:                 Print DKVP-formatted pairwise-distance data.\n");
    o.printf(" pairwise-distances:  Compute pairwise distances given two filenames\n");
    o.printf(" bits:                Format hashes as 2D binary matrices\n");
    o.printf(" lbits:               Format hashes as 1D binary vectors\n");
    o.printf(" words:               Format hashes as space-delimited 16-bit words in hex\n");
    o.printf(" hashcodes:           Format Java .hashCode() for each hash\n");
    o.printf(" fuzz {n}:            Randomly flip n bits (with replacement) in the input hashes.\n");
    o.printf(" pathwise-dedupe {d}: Dedupe pathwise with distance threshold d.\n");
    o.printf(" int64:               Format hashes as comma-separated sets of 4 64-bit integers.\n");
    System.exit(rc);
  }

  // ----------------------------------------------------------------
  public static void main(String[] args) {

    // Parse command-line flags. I'm explicitly not using gflags or other such
    // libraries, to minimize the number of external dependencies for this
    // project.
    if (args.length < 1)
      usage(1);
    String verb = args[0];
    args = Arrays.copyOfRange(args, 1, args.length);
    if (verb.equals("-h") || verb.equals("--help")) {
      usage(0);

    } else if (verb.equals("norms")) {
      doNorms(verb, args);
    } else if (verb.equals("slotnorms")) {
      doSlotNorms(verb, args);
    } else if (verb.equals("deltas")) {
      doDeltas(verb, args);
    } else if (verb.equals("axors")) {
      doAdjacentXors(verb, args);
    } else if (verb.equals("fxors")) {
      doXorsFromFirst(verb, args);
    } else if (verb.equals("matrix")) {
      doMatrix(verb, args, false);
    } else if (verb.equals("cij")) {
      doMatrix(verb, args, true);
    } else if (verb.equals("pairwise-distances")) {
      doPairwiseDistances(verb, args);
    } else if (verb.equals("bits")) {
      doBits(verb, args);
    } else if (verb.equals("lbits")) {
      doLbits(verb, args);
    } else if (verb.equals("words")) {
      doWords(verb, args);
    } else if (verb.equals("hashcodes")) {
      doHashCodes(verb, args);
    } else if (verb.equals("fuzz")) {
      doFuzz(verb, args);
    } else if (verb.equals("pathwise-dedupe")) {
      doPathwiseDedupe(verb, args);
    } else if (verb.equals("int64")) {
      doInt64Vals(verb, args);

    } else {
      usage(1);
    }
  }

  // ----------------------------------------------------------------
  static void doNorms(String verb, String[] args) {
    Vector<Hash256> hashes = new Vector<Hash256>();
    HashReaderUtil.loadHashesFromFilesOrDie(PROGNAME, args, hashes);
    for (Hash256 hash : hashes) {
      System.out.printf("%s %d\n", hash.toString(), hash.hammingNorm());
    }
  }

  // ----------------------------------------------------------------
  static void doSlotNorms(String verb, String[] args) {
    Vector<Hash256> hashes = new Vector<Hash256>();
    HashReaderUtil.loadHashesFromFilesOrDie(PROGNAME, args, hashes);
    for (Hash256 hash : hashes) {
      System.out.printf("%s", hash.toString());
      for (int i = 0; i < Hash256.HASH256_NUM_SLOTS; i++) {
        System.out.printf(" %2d", Hash256.hammingNorm16(hash.w[i]));
      }
      System.out.printf("\n");
    }
  }

  // ----------------------------------------------------------------
  static void doDeltas(String verb, String[] args) {
    Vector<Hash256> hashes = new Vector<Hash256>();
    HashReaderUtil.loadHashesFromFilesOrDie(PROGNAME, args, hashes);
    int n = hashes.size();
    for (int i = 0; i < n; i++) {
      if (i == 0) {
        System.out.printf("%s\n", hashes.get(i).toString());
      } else {
        System.out.printf("%s %d\n",
          hashes.get(i).toString(), hashes.get(i).hammingDistance(hashes.get(i-1)));
      }
    }
  }

  // ----------------------------------------------------------------
  static void doAdjacentXors(String verb, String[] args) {
    Vector<Hash256> hashes = new Vector<Hash256>();
    HashReaderUtil.loadHashesFromFilesOrDie(PROGNAME, args, hashes);
    int n = hashes.size();
    for (int i = 1; i < n; i++) {
      Hash256 x = hashes.get(i-1).bitwiseXOR(hashes.get(i));
      System.out.printf("%s\n", x.toString());
    }
  }

  // ----------------------------------------------------------------
  static void doXorsFromFirst(String verb, String[] args) {
    Vector<Hash256> hashes = new Vector<Hash256>();
    HashReaderUtil.loadHashesFromFilesOrDie(PROGNAME, args, hashes);
    int n = hashes.size();
    for (int i = 1; i < n; i++) {
      Hash256 x = hashes.get(0).bitwiseXOR(hashes.get(i));
      System.out.printf("%s\n", x.toString());
    }
  }

  // ----------------------------------------------------------------
  static void doMatrix(String verb, String[] args, boolean doCij) {
    Vector<Hash256> hashes1 = new Vector<Hash256>();
    Vector<Hash256> hashes2 = new Vector<Hash256>();

    if (args.length == 0) {
      HashReaderUtil.loadHashesFromStdinOrDie(PROGNAME, hashes1);
      hashes2 = hashes1;
    } else if (args.length == 1) {
      HashReaderUtil.loadHashesFromFileOrDie(PROGNAME, args[0], hashes1);
      hashes2 = hashes1;
    } else if (args.length == 2) {
      HashReaderUtil.loadHashesFromFileOrDie(PROGNAME, args[0], hashes1);
      HashReaderUtil.loadHashesFromFileOrDie(PROGNAME, args[1], hashes2);
    } else {
      usage(1);
    }

    int m = hashes1.size();
    int n = hashes2.size();

    if (doCij) {
      for (int i = 0; i < m; i++) {
        for (int j = 0; j < n; j++) {
          System.out.printf("ci=%s,cj=%s,i=%d,j=%d,d=%d\n",
            hashes1.get(i).toString(),
            hashes2.get(j).toString(),
            i, j,
            hashes1.get(i).hammingDistance(hashes2.get(j)));
        }
      }
    } else {
      for (int i = 0; i < m; i++) {
        for (int j = 0; j < n; j++) {
          System.out.printf(" %3d", hashes1.get(i).hammingDistance(hashes2.get(j)));
        }
        System.out.printf("\n");
      }
    }
  }

  // ----------------------------------------------------------------
  static void doPairwiseDistances(String verb, String[] args) {
    if (args.length != 2) {
      System.err.printf("%s %s: need two filenames.\n", PROGNAME, verb);
      System.exit(1);
    }
    Vector<Hash256> hashes1 = new Vector<Hash256>();
    Vector<Hash256> hashes2 = new Vector<Hash256>();

    HashReaderUtil.loadHashesFromFileOrDie(PROGNAME, args[0], hashes1);
    HashReaderUtil.loadHashesFromFileOrDie(PROGNAME, args[1], hashes2);
    int n1 = hashes1.size();
    int n2 = hashes2.size();

    for (int i = 0; i < n1 && i < n2; i++) {
      System.out.printf("%3d\n", hashes1.get(i).hammingDistance(hashes2.get(i)));
    }
  }

  // ----------------------------------------------------------------
  static void doBits(String verb, String[] args) {
    Vector<Hash256> hashes = new Vector<Hash256>();
    HashReaderUtil.loadHashesFromFilesOrDie(PROGNAME, args, hashes);
    for (Hash256 hash : hashes) {
      hash.dumpBits(System.out);
    }
  }

  // ----------------------------------------------------------------
  static void doLbits(String verb, String[] args) {
    Vector<Hash256> hashes = new Vector<Hash256>();
    HashReaderUtil.loadHashesFromFilesOrDie(PROGNAME, args, hashes);
    for (Hash256 hash : hashes) {
      hash.dumpBitsAcross(System.out);
    }
  }

  // ----------------------------------------------------------------
  static void doWords(String verb, String[] args) {
    Vector<Hash256> hashes = new Vector<Hash256>();
    HashReaderUtil.loadHashesFromFilesOrDie(PROGNAME, args, hashes);
    for (Hash256 hash : hashes) {
      hash.dumpWords(System.out);
    }
  }

  // ----------------------------------------------------------------
  static void doHashCodes(String verb, String[] args) {
    Vector<Hash256> hashes = new Vector<Hash256>();
    HashReaderUtil.loadHashesFromFilesOrDie(PROGNAME, args, hashes);
    for (Hash256 hash : hashes) {
      System.out.printf("%s %08x\n", hash.toString(), hash.hashCode());
    }
  }

  // ----------------------------------------------------------------
  static void doFuzz(String verb, String[] args) {
    if (args.length < 1) {
      System.err.printf("%s %s: need number of bits to fuzz.\n", PROGNAME, verb);
      System.exit(1);
    }

    int numErrorBits = 0;
    try {
      numErrorBits = Integer.parseInt(args[0]);
    } catch (NumberFormatException e) {
      System.err.printf("%s %s: couldn't scan \"%s\" as number of bits to fuzz.\n",
        PROGNAME, verb, args[0]);
      System.exit(1);
    }
    args = Arrays.copyOfRange(args, 1, args.length);

    Vector<Hash256> hashes = new Vector<Hash256>();
    HashReaderUtil.loadHashesFromFilesOrDie(PROGNAME, args, hashes);
    for (Hash256 hash : hashes) {
      hash = hash.fuzz(numErrorBits);
      System.out.printf("%s\n", hash.toString());
    }
  }

  // ----------------------------------------------------------------
  static void doPathwiseDedupe(String verb, String[] args) {
    if (args.length < 1) {
      System.err.printf("%s %s: need distance threshold for pathwise dedupe.\n", PROGNAME, verb);
      System.exit(1);
    }

    int threshold = 0;
    try {
      threshold = Integer.parseInt(args[0]);
    } catch (NumberFormatException e) {
      System.err.printf("%s %s: couldn't scan \"%s\" as number of bits to fuzz.\n",
        PROGNAME, verb, args[0]);
      System.exit(1);
    }
    args = Arrays.copyOfRange(args, 1, args.length);

    Vector<Hash256AndMetadata<String>> vectorOfPairs = new Vector<Hash256AndMetadata<String>>();
    HashReaderUtil.loadHashesAndMetadataFromFilesOrDie(PROGNAME, args, vectorOfPairs);

    Hash256 prev = null;
    for (Hash256AndMetadata<String> pair : vectorOfPairs) {
      Hash256 hash = pair.hash;

      boolean printIt = false;
      int d = 0;
      if (prev == null) { // First hash: must print
        prev = hash;
        printIt = true;
      } else { // Subsequent hash
        d = hash.hammingDistance(prev);
        if (d >= threshold) {
          // New
          printIt = true;
          prev = hash;
        } else {
          // Dupe
          printIt = false;
        }
      }

      if (printIt) {
        System.out.printf("hash=%s,dd=%d,%s\n", hash.toString(), d, pair.metadata);
      }
    }
  }

  // ----------------------------------------------------------------
  static void doInt64Vals(String verb, String[] args) {
    Vector<Hash256> hashes = new Vector<Hash256>();
    HashReaderUtil.loadHashesFromFilesOrDie(PROGNAME, args, hashes);
    for (Hash256 hash256 : hashes) {
      HashInt64 hash = new HashInt64(hash256);
      hash.dumpVals(System.out);
    }
  }
}
