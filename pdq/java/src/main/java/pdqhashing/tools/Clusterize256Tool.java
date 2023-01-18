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
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
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
 *  output. It's slower and is nice for one-stop shopping on a few thousand
 *  hashes.
 *
 * * The latter is streaming, uses less memory, and is far faster. It does not
 *   produce cluster sizes on output. (Those need to be computed as an
 *   afterpass.) It necessary for operating on millions of hashes.
 *
 *
 * By default, a 'snowball' clusterer is used: given first-encountered hash h1,
 * all subsequent hashes within the specified distance threshold of h1 are
 * listed within that cluster. This is transitive: if h1 is near h2, h2 is
 * near h3, and h3 is near h4, then all four are clustered together even if
 * h1 is not near h4.
 *
 * The non-snowball option means that for each hash, all other hashes within
 * specified radius are printed. This allows for duplicate outputs.
 *
 * See pdqhashing/utils/HashReaderUtil.java for file-format information.
 *
 * See the usage function for more usage information.
 * ================================================================
 */

public class Clusterize256Tool {
private static final String PROGNAME = "Clusterize256Tool";
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
    o.printf("-v|--verbose Be verbose.\n");
    o.printf("-b|--brute-force-query Use linear search not MIH.\n");
    o.printf("-s|--separate-clusters Print a blank line between clusters.\n");
    o.printf("--snowball Print each hash once, with transitive clustering.\n");
    o.printf("  This is the default.\n");
    o.printf("--non-snowball For each hash, print all other hashes within distance threshold.\n");
    o.printf("-d {n}       Distance threshold: default %d.\n",
      DEFAULT_PDQ_DISTANCE_THRESHOLD);
    o.printf("--trace {n}  Print to stderr every n items. Default off.\n");
    System.exit(rc);
  }

  // ----------------------------------------------------------------
  public static void main(String[] args) {
    boolean verbose = false;
    boolean separateClusters = false;
    boolean snowball = true;
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
      } else if (args[argi].equals("-v") || args[argi].equals("--verbose")) {
        verbose = true;
        argi++;
      } else if (args[argi].equals("-s") || args[argi].equals("--separate-clusters")) {
        separateClusters = true;
        argi++;
      } else if (args[argi].equals("--snowball")) {
        snowball = true;
        argi++;
      } else if (args[argi].equals("--non-snowball")) {
        snowball = false;
        argi++;
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
    // Load input hashes+metadata

    Vector<Hash256AndMetadata<String>> vectorOfPairs = new Vector<Hash256AndMetadata<String>>();

    HashReaderUtil.loadHashesAndMetadataFromFilesOrDie(PROGNAME, args, vectorOfPairs);

    if (verbose) {
      System.out.printf("ORIGINAL VECTOR OF PAIRS:\n");
      for (Hash256AndMetadata<String> pair : vectorOfPairs) {
        System.out.printf("%s,%s\n", pair.hash.toString(), pair.metadata);
      }
      System.out.printf("\n");
    }

    //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    // Build the mutually-indexed hash

    MIH256<String> mih = new MIH256<String>();
    // We could insertAll, but instead loop so we can trace.
    // mih.insertAll(vectorOfPairs);
    int i = 0;
    for (Hash256AndMetadata<String> pair : vectorOfPairs) {
      if (traceCount > 0) {
        if ((i % traceCount) == 0) {
          System.err.printf("i %d\n", i);
        }
      }
      i++;
      mih.insert(pair.hash, pair.metadata);
    }

    if (verbose) {
      System.out.printf("MIH:\n");
      mih.dump(System.out);
      System.out.printf("\n");
    }

    //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    // Clusterize
    if (snowball) {
      snowballClusterize(vectorOfPairs, mih,
        separateClusters, traceCount, doBruteForceQuery, distanceThreshold);
    }
    else {
      radiallyClusterize(vectorOfPairs, mih,
        separateClusters, traceCount, doBruteForceQuery, distanceThreshold);
    }
  }

  // ----------------------------------------------------------------
  private static void snowballClusterize(
    Vector<Hash256AndMetadata<String>> vectorOfPairs,
    MIH256<String> mih,
    boolean separateClusters,
    int  traceCount,
    boolean  doBruteForceQuery,
    int  distanceThreshold
  ) {

    Map<String,Set<String>> adjacencyMatrix = new LinkedHashMap<String,Set<String>>();
    Map<String,Hash256> metadataToHashes = new LinkedHashMap<String,Hash256>();

    // INGEST DATA
    int i = 0;
    for (Hash256AndMetadata<String> hashAndMetadata : vectorOfPairs) {
      Hash256 needleHash = hashAndMetadata.hash;
      String needleMetadata = hashAndMetadata.metadata;

      if (traceCount > 0) {
        if ((i % traceCount) == 0) {
          System.err.printf("o %d\n", i);
        }
      }
      i++;

      Vector<Hash256AndMetadata<String>> matches = new Vector<Hash256AndMetadata<String>>();
      try {
        if (doBruteForceQuery) {
          mih.bruteForceQueryAll(needleHash, distanceThreshold, matches);
        } else {
          mih.queryAll(needleHash, distanceThreshold, matches);
        }
      } catch (MIHDimensionExceededException e) {
        System.err.printf("%s: %s\n", PROGNAME, e.getErrorMessage());
        System.exit(1);
      }

      metadataToHashes.put(needleMetadata, needleHash);
      for (Hash256AndMetadata<String> match : matches) {
        Hash256 haystackHash = match.hash;
        String haystackMetadata = match.metadata;
        metadataToHashes.put(haystackMetadata, haystackHash);

        if (adjacencyMatrix.get(needleMetadata) == null) {
          adjacencyMatrix.put(needleMetadata, new LinkedHashSet<String>());
        }
        adjacencyMatrix.get(needleMetadata).add(haystackMetadata);

        if (adjacencyMatrix.get(haystackMetadata) == null) {
          adjacencyMatrix.put(haystackMetadata, new LinkedHashSet<String>());
        }
        adjacencyMatrix.get(haystackMetadata).add(needleMetadata);
      }
    }

    // IDENTIFY CLUSTER REPRESENTATIVES

    // For the sake of discussion suppose the item IDs are A, B, C, D, E.
    // Input data includes the adjacency matrix
    //
    //     A B C D E
    //   A * . * * .
    //   B . * . * .
    //   C * . * . .
    //   D * * . * .
    //   E . . . . *
    //
    // We expect to get [A,B,C,D] as one equivalence class and [E] as the other.
    // Representatives are just the first-found, e.g. A and E respectively.

    Map<String,String> metadatasToClusterRepresentatives = new LinkedHashMap<String,String>();

    // For each row of the adjacency matrix:
    for (Map.Entry<String,Set<String>> row : adjacencyMatrix.entrySet()) {
      String metadata_i = row.getKey();
      Set<String> metadata_js = row.getValue();

      // Already-visited items, found by off-diagonal on a previous row
      if (metadatasToClusterRepresentatives.get(metadata_i) != null) {
        continue;
      }

      // Each row of the adjacency matrix contributes to an equivalence class.
      // E.g. the top row of the above example gives [A,C,D]. The only question
      // is whether this is standalone or part of something already seen. For
      // example, on the first row we get [A,C,D]. On the second row we have
      // [B,D] but D was already seen.

      // Find a representative for this item: Either the first-found in the
      // row, or an already-seen (if there is one).
      String representative = metadata_i; // E.g. A on first row, B on second row
      for (String metadata_j : metadata_js) {
        String other = metadatasToClusterRepresentatives.get(metadata_j);
        if (other != null) {
          representative = other;
          break;
        }
      }

      // Mark all the items in the current row as having that representative
      for (String metadata_j : metadata_js) {
        metadatasToClusterRepresentatives.put(metadata_j, representative);
      }
    }

    // FORM EQUIVALENCE CLASSES
    Map<String,Set<String>> equivalenceClasses = new LinkedHashMap<String,Set<String>>();
    for (Map.Entry<String,Hash256> entry : metadataToHashes.entrySet()) {
      String metadata = entry.getKey();
      String representative = metadatasToClusterRepresentatives.get(metadata);

      if (equivalenceClasses.get(representative) == null) {
        equivalenceClasses.put(representative, new LinkedHashSet<String>());
      }
      equivalenceClasses.get(representative).add(metadata);
    }

    // OUTPUT
    int clusterIndex = 0;
    for (Map.Entry<String,Set<String>> entry : equivalenceClasses.entrySet()) {
      Set<String> equivalenceClass = entry.getValue();
      clusterIndex++;
      int clusterSize = equivalenceClass.size();

      if (separateClusters && clusterIndex > 1) {
        System.out.println();
      }

      for (String metadata : equivalenceClass) {
        System.out.printf("clidx=%d,clusz=%d,hash=%s,%s\n",
          clusterIndex,
          clusterSize,
          metadataToHashes.get(metadata).toString(),
          metadata);
      }
    }
  }

  // ----------------------------------------------------------------
  private static void radiallyClusterize(
    Vector<Hash256AndMetadata<String>> vectorOfPairs,
    MIH256<String> mih,
    boolean separateClusters,
    int  traceCount,
    boolean  doBruteForceQuery,
    int  distanceThreshold
  ) {

    int clusterIndex = 0;

    int i = 0;
    for (Hash256AndMetadata<String> needlePair : vectorOfPairs) {
      Hash256 needleHash = needlePair.hash;
      String needleMetadata = needlePair.metadata;

      if (traceCount > 0) {
        if ((i % traceCount) == 0) {
          System.err.printf("o %d\n", i);
        }
      }
      i++;

      Vector<Hash256AndMetadata<String>> matches = new Vector<Hash256AndMetadata<String>>();
      try {
        if (doBruteForceQuery) {
          mih.bruteForceQueryAll(needleHash, distanceThreshold, matches);
        } else {
          mih.queryAll(needleHash, distanceThreshold, matches);
        }
      } catch (MIHDimensionExceededException e) {
        System.err.printf("%s: %s\n", PROGNAME, e.getErrorMessage());
        System.exit(1);
      }

      int clusterSize = matches.size();
      if (clusterSize > 0) {
        clusterIndex++;
        if (clusterIndex > 1 && separateClusters) {
          System.out.println();
        }
        for (Hash256AndMetadata<String> hayfiberPair : matches) {
          Hash256 hayfiberHash = hayfiberPair.hash;
          String hayfiberMetadata = hayfiberPair.metadata;
          int d = needleHash.hammingDistance(hayfiberHash);
          System.out.printf("clidx=%d,clusz=%d,hash1=%s,hash2=%s,d=%d,%s\n",
            clusterIndex,
            clusterSize,
            needleHash.toString(),
            hayfiberHash.toString(),
            d,
            hayfiberMetadata);
        }
      }

      System.out.flush();
    }
  }
}
