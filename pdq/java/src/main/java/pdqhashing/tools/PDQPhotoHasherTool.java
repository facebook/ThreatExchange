// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

package pdqhashing.tools;

import pdqhashing.hasher.PDQHasher;
import pdqhashing.types.Hash256;
import pdqhashing.types.HashAndQuality;
import pdqhashing.types.HashesAndQuality;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.IOException;
import java.io.PrintStream;

/**
 * Ops/demo tool for computing PDQ hashes of image files (JPEG, PNG, etc.)
 */
public class PDQPhotoHasherTool {
  private static final String PROGNAME = "PDQPhotoHasherTool";

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
    o.printf("Usage: %s [options] {one or more filenames}\n", PROGNAME);
    o.printf("Supported filetypes are whatever javax.imageio's load method can handle,\n");
    o.printf("e.g. JPEG and PNG.\n");
    o.printf("\n");
    o.printf("Options:\n");
    o.printf("-i|--files-on-stdin: Take filenames from stdin, in which\n");
    o.printf("  case there must be no filenames on the command line.\n");
    o.printf("-d|--details: Print norm, delta, etc; else print just hash, quality, and filename.\n");
    o.printf("--pdqdih: Print all 8 dihedral-transform hashes.\n");
    o.printf("--pdqdih-across: Print all 8 dihedral-transform hashes, all on one line.\n");
    o.printf("--no-timings: Don't compute timing information.\n");
    o.printf("-k: Continue to next image after image errors, but still exit 1 afterward.\n");
    System.exit(rc);
  }

  public static void main(String[] args) {
    boolean filesOnStdin = false;
    boolean doPDQHash = true;
    boolean doPDQDih = false;
    boolean doPDQDihAcross = false;
    boolean doDetailedOutput = false;
    boolean doTimings = true;
    boolean keepGoingAfterErrors = false;

    // Parse command-line flags. I'm explicitly not using gflags or other such
    // libraries, to minimize the number of external dependencies for this
    // project.
    int argi = 0;
    int argc = args.length;
    for (argi = 0; argi < argc; argi++) {
      if (!args[argi].startsWith("-")) {
        break;
      }

      if (args[argi].equals("-h") || args[argi].equals("--help")) {
        usage(0);

      } else if (args[argi].equals("-i") || args[argi].equals("--files-on-stdin")) {
        filesOnStdin  = true;
        continue;

      } else if (args[argi].equals("-d") || args[argi].equals("--details")) {
        doDetailedOutput  = true;
        continue;

      } else if (args[argi].equals("--no-timings")) {
        doTimings  = false;
        continue;

      } else if (args[argi].equals("--pdq")) {
        doPDQHash = true;
        doPDQDih  = false;
        continue;

      } else if (args[argi].equals("--pdqdih")) {
        doPDQHash = false;
        doPDQDih = true;
        doPDQDihAcross = false;
        continue;

      } else if (args[argi].equals("--pdqdih-across")) {
        doPDQHash = false;
        doPDQDih = true;
        doPDQDihAcross = true;
        continue;

      } else if (args[argi].equals("-k")) {
        keepGoingAfterErrors = true;
        continue;

      } else {
        usage(1);
      }
    }

    PDQHasher pdqHasher = new PDQHasher();

    Context context = new Context(
      0, // numPDQHash
      null, // pdqHashPrev
      false); // hadError

    // Iterate over image-file names.  One file at a time, compute per-file hash
    // and hamming distance to previous. (E.g. for video frame-taps).
    if (filesOnStdin) {
      if (argi < argc) {
        usage(1);
      }

      BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
      String filename = null;
      int lno = 1;
      try {
        while ((filename = reader.readLine()) != null) { // In Java, line-terminators already stripped for us
          lno++;
          context.numPDQHash++;
          processFile(pdqHasher, filename, doPDQHash, doPDQDih, doPDQDihAcross,
            doDetailedOutput, doTimings, keepGoingAfterErrors, context);
          System.out.flush();
        }
      } catch (IOException e) {
        System.err.printf("Couldn't read line %d of standard input.\n", lno);
        System.exit(1);
      }
    } else {
      if (argi >= argc) {
        usage(1);
      }
      for ( ; argi < argc; argi++) {
        String filename = args[argi];
        context.numPDQHash++;
        processFile(pdqHasher, filename, doPDQHash, doPDQDih, doPDQDihAcross,
          doDetailedOutput, doTimings, keepGoingAfterErrors, context);
        System.out.flush();
      }
    }

    if (context.hadError) {
      System.exit(1);
    }

  }

  // ----------------------------------------------------------------
  static void processFile(
    PDQHasher pdqHasher,
    String filename,
    boolean doPDQHash,
    boolean doPDQDih,
    boolean doPDQDihAcross,
    boolean doDetailedOutput,
    boolean doTimings,
    boolean keepGoingAfterErrors,
    Context context)
  {
    Hash256 hash = null;
    HashAndQuality hashAndQuality = null;
    HashesAndQuality dihedralBag = null;
    int quality;
    int norm;
    int delta;
    PDQHasher.HashingMetadata hashingMetadata = new PDQHasher.HashingMetadata ();

    if (doPDQHash) {

      try {
        hashAndQuality = pdqHasher.fromFile(filename, hashingMetadata);
      } catch (IOException e) {
        context.hadError = true;
        System.err.printf("%s: could not read image file %s.\n", PROGNAME, filename);
        if (keepGoingAfterErrors) {
          return;
        } else {
          System.exit(1);
        }
      }
      hash = hashAndQuality.getHash();
      quality = hashAndQuality.getQuality();

      norm = hash.hammingNorm();
      delta = (context.numPDQHash == 1)
        ? 0
        : hash.hammingDistance(context.pdqHashPrev);

      if (!doDetailedOutput) {
        System.out.printf("%s,%d,%s\n", hash.toString(), quality, filename);
      } else {
        System.out.printf("hash=%s",     hash.toString());
        System.out.printf(",norm=%d",    norm);
        System.out.printf(",delta=%d",   delta);
        System.out.printf(",quality=%d", quality);
        if (doTimings) {
          System.out.printf(",dims=%d", hashingMetadata.imageHeightTimesWidth);
          System.out.printf(",readSeconds=%.6f", hashingMetadata.readSeconds);
          System.out.printf(",hashSeconds=%.6f", hashingMetadata.hashSeconds);
        }
        System.out.printf(",filename=%s\n", filename);
      }

      context.pdqHashPrev = hash;
    }

    if (doPDQDih) {
      try {
        dihedralBag = pdqHasher.dihedralFromFile(
          filename, 
          hashingMetadata,
          PDQHasher.PDQ_DO_DIH_ALL
        );
      } catch (IOException e) {
        context.hadError = true;
        System.err.printf("%s: could not read image file %s.\n", PROGNAME, filename);
        if (keepGoingAfterErrors) {
          return;
        } else {
          System.exit(1);
        }
      }

      if (!doDetailedOutput) {
        if (doPDQDihAcross) {
          System.out.printf("%s,%s,%s,%s,%s,%s,%s,%s,%d,%s\n",
            dihedralBag.hash.toString(),
            dihedralBag.hashRotate90.toString(),
            dihedralBag.hashRotate180.toString(),
            dihedralBag.hashRotate270.toString(),
            dihedralBag.hashFlipX.toString(),
            dihedralBag.hashFlipY.toString(),
            dihedralBag.hashFlipPlus1.toString(),
            dihedralBag.hashFlipMinus1.toString(),
            dihedralBag.quality,
            filename);
        } else {
          int bquality = dihedralBag.quality;
          System.out.printf("%s,%d,%s\n", dihedralBag.hash.toString(), bquality, filename);
          System.out.printf("%s,%d,%s\n", dihedralBag.hashRotate90.toString(), bquality, filename);
          System.out.printf("%s,%d,%s\n", dihedralBag.hashRotate180.toString(), bquality, filename);
          System.out.printf("%s,%d,%s\n", dihedralBag.hashRotate270.toString(), bquality, filename);
          System.out.printf("%s,%d,%s\n", dihedralBag.hashFlipX.toString(), bquality, filename);
          System.out.printf("%s,%d,%s\n", dihedralBag.hashFlipY.toString(), bquality, filename);
          System.out.printf("%s,%d,%s\n", dihedralBag.hashFlipPlus1.toString(), bquality, filename);
          System.out.printf("%s,%d,%s\n", dihedralBag.hashFlipMinus1.toString(), bquality, filename);
        }
      } else {
        if (doPDQDihAcross) {
          System.out.printf("hash=%s", dihedralBag.hash.toString());
          System.out.printf(",quality=%d", dihedralBag.quality);
          if (doTimings) {
            System.out.printf(",dims=%d", hashingMetadata.imageHeightTimesWidth);
            System.out.printf(",readSeconds=%.6f", hashingMetadata.readSeconds);
            System.out.printf(",hashSeconds=%.6f", hashingMetadata.hashSeconds);
          }

          System.out.printf(",orig=%s", dihedralBag.hash.toString());
          System.out.printf(",rot90=%s", dihedralBag.hashRotate90.toString());
          System.out.printf(",rot180=%s", dihedralBag.hashRotate180.toString());
          System.out.printf(",rot270=%s", dihedralBag.hashRotate270.toString());
          System.out.printf(",flipx=%s", dihedralBag.hashFlipX.toString());
          System.out.printf(",flipy=%s", dihedralBag.hashFlipY.toString());
          System.out.printf(",flipp=%s", dihedralBag.hashFlipPlus1.toString());
          System.out.printf(",flipm=%s", dihedralBag.hashFlipMinus1.toString());
          System.out.printf(",filename=%s\n", filename);

        } else {
          System.out.printf("hash=%s",       dihedralBag.hash.toString());
          System.out.printf(",quality=%d", dihedralBag.quality);
          if (doTimings) {
            System.out.printf(",dims=%d", hashingMetadata.imageHeightTimesWidth);
            System.out.printf(",readSeconds=%.6f", hashingMetadata.readSeconds);
            System.out.printf(",hashSeconds=%.6f", hashingMetadata.hashSeconds);
          }
          System.out.printf(",filename=%s\n", filename);

          System.out.printf("hash=%s,xform=orig,filename=%s\n",
            dihedralBag.hash.toString(), filename);
          System.out.printf("hash=%s,xform=rot90,filename=%s\n",
            dihedralBag.hashRotate90.toString(), filename);
          System.out.printf("hash=%s,xform=rot180,filename=%s\n",
            dihedralBag.hashRotate180.toString(), filename);
          System.out.printf("hash=%s,xform=rot270,filename=%s\n",
            dihedralBag.hashRotate270.toString(), filename);
          System.out.printf("hash=%s,xform=flipx,filename=%s\n",
            dihedralBag.hashFlipX.toString(), filename);
          System.out.printf("hash=%s,xform=flipy,filename=%s\n",
            dihedralBag.hashFlipY.toString(), filename);
          System.out.printf("hash=%s,xform=flipp,filename=%s\n",
            dihedralBag.hashFlipPlus1.toString(), filename);
          System.out.printf("hash=%s,xform=flipm,filename=%s\n",
            dihedralBag.hashFlipMinus1.toString(), filename);
          }
      }
      context.pdqHashPrev = dihedralBag.hash.clone();
    }
  }
}
