// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

package pdqhashing.utils;

import pdqhashing.types.Hash256;
import pdqhashing.types.Hash256AndMetadata;
import pdqhashing.types.PDQHashFormatException;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.Vector;

/**
 * Hashes with metadata
 *
 * If zero filenames are provided, stdin is read.  Files should have one
 * hex-formatted 256-bit hash per line, optionally prefixed by "hash=". If
 * a comma and other text follows the hash, it is used as metadata; else,
 * a counter is used as the metadata.
 *
 * Example:
 * ```
 * f8f8f0cce0f4e84d0e370a22028f67f0b36e2ed596623e1d33e6339c4e9c9b22
 * b0a10efd71cc3f429413d48d0ffffe12e34e0e17ada952a9d29684210aa9e5af
 * adad5a64b5a142e55362a09057dacd5ae63b847fc23794b766b319361fc93188
 * a5f4a457a48995e8c9065c275aaa5498b61ba4bdf8fcf80387c32f8b0bfc4f05
 * f8f80f31e0f417b00e37f5cd028f980fb36ed02a9662c1e233e6cc634e9c64dd
 * 8dad2599b1a1bd1853625f6553da32a1e63b7280c2374b4866b366c91bc9ce77
 * f0a1f102f1dcc0bd9c5309720fff018de34ef1e8ada9a956d2967ade0ea91a50
 * a5f05ba8a4896a17c106a3da5aaaab07b61b5b42f8fc07fc83c3d0740bfcb0fa
 * ```
 *
 * Example:
 * ```
 * f8f8f0cce0f4e84d0e370a22028f67f0b36e2ed596623e1d33e6339c4e9c9b22,file1.jpg
 * b0a10efd71cc3f429413d48d0ffffe12e34e0e17ada952a9d29684210aa9e5af,file2.jpg
 * adad5a64b5a142e55362a09057dacd5ae63b847fc23794b766b319361fc93188,file3.jpg
 * a5f4a457a48995e8c9065c275aaa5498b61ba4bdf8fcf80387c32f8b0bfc4f05,file4.jpg
 * f8f80f31e0f417b00e37f5cd028f980fb36ed02a9662c1e233e6cc634e9c64dd,file5.jpg
 * 8dad2599b1a1bd1853625f6553da32a1e63b7280c2374b4866b366c91bc9ce77,file6.jpg
 * f0a1f102f1dcc0bd9c5309720fff018de34ef1e8ada9a956d2967ade0ea91a50,file7.jpg
 * a5f05ba8a4896a17c106a3da5aaaab07b61b5b42f8fc07fc83c3d0740bfcb0fa,file8.jpg
 * ```
 *
 * Example:
 * ```
 * hash=f8f8...9b22,norm=128,delta=0,quality=100,filename=file1.jpg
 * hash=b0a1...e5af,norm=128,delta=124,quality=100,filename=file2.jpg
 * hash=adad...3188,norm=128,delta=122,quality=100,filename=file3.jpg
 * hash=a5f4...4f05,norm=128,delta=118,quality=100,filename=file4.jpg
 * hash=f8f8...64dd,norm=128,delta=124,quality=100,filename=file5.jpg
 * hash=8dad...ce77,norm=128,delta=122,quality=100,filename=file6.jpg
 * hash=f0a1...1a50,norm=128,delta=124,quality=100,filename=file7.jpg
 * hash=a5f0...b0fa,norm=128,delta=124,quality=100,filename=file8.jpg
 * ```
 */

public class HashReaderUtil {

  // ----------------------------------------------------------------
  public static Hash256AndMetadata<String> loadHashAndMetadataFromStream(
    BufferedReader reader,
    int lineCounter)
      throws IOException, PDQHashFormatException
  {
    String prefix = "hash=";
    String line = reader.readLine();
    Hash256 hash = null;
    String metadata = null;

    if (line == null) {
      return null;
    }

    // Split hash from metadata on comma
    String[] pair = line.split(",", 2);
    if (pair.length == 1) {
      metadata = "idx=" + Integer.toString(lineCounter);
    } else {
      metadata = pair[1];
    }
    if (pair[0].startsWith(prefix)) {
      hash = Hash256.fromHexString(pair[0].replace(prefix, ""));
    } else {
        hash = Hash256.fromHexString(pair[0]);
    }
    return new Hash256AndMetadata<String>(hash, metadata);
  }

  // ----------------------------------------------------------------
  public static void loadHashesAndMetadataFromStream(
    BufferedReader reader,
    Vector<Hash256AndMetadata<String>> vectorOfPairs)
      throws IOException, PDQHashFormatException
  {
    while (true) {
      int counter = vectorOfPairs.size() + 1;
      Hash256AndMetadata<String> pair = loadHashAndMetadataFromStream(reader, counter);
      if (pair == null) {
        break;
      }
      vectorOfPairs.add(pair);
    }
  }

  public static void loadHashesAndMetadataFromStreamOrDie(
    String programName,
    BufferedReader reader,
    Vector<Hash256AndMetadata<String>> vectorOfPairs)
  {
    try {
      loadHashesAndMetadataFromStream(reader, vectorOfPairs);
    } catch (IOException e) {
      System.err.printf("%s: could not read hashes from input stream.\n",
        programName);
      System.exit(1);
    } catch (PDQHashFormatException e) {
      System.err.printf("%s: could not parse hash \"%s\" from input stream.\n",
        programName, e.getUnacceptableInput());
      System.exit(1);
    }
  }

  // ----------------------------------------------------------------
  public static void loadHashesAndMetadataFromFile(
    String filename,
    Vector<Hash256AndMetadata<String>> vectorOfPairs)
      throws IOException, PDQHashFormatException
  {
    BufferedReader reader = new BufferedReader(new FileReader(filename));
    loadHashesAndMetadataFromStream(reader, vectorOfPairs);
    reader.close();
  }

  public static void loadHashesAndMetadataFromFileOrDie(
    String programName,
    String filename,
    Vector<Hash256AndMetadata<String>> vectorOfPairs)
  {
    try {
      loadHashesAndMetadataFromFile(filename, vectorOfPairs);
    } catch (IOException e) {
      System.err.printf("%s: could not read hashes from file \"%s\".\n",
        programName, filename);
      System.exit(1);
    } catch (PDQHashFormatException e) {
      System.err.printf("%s: malformed hash \"%s\" in file \"%s\".\n",
        programName, e.getUnacceptableInput(), filename);
      System.exit(1);
    }
  }

  // ----------------------------------------------------------------
  public static void loadHashesAndMetadataFromFiles(
    String[] filenames,
    Vector<Hash256AndMetadata<String>> vectorOfPairs)
      throws IOException, PDQHashFormatException
  {
    if (filenames.length == 0) {
      BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
      loadHashesAndMetadataFromStream(reader, vectorOfPairs);
    } else {
      for (String filename : filenames) {
        loadHashesAndMetadataFromFile(filename, vectorOfPairs);
      }
    }
  }

  public static void loadHashesAndMetadataFromFilesOrDie(
    String programName,
    String[] filenames,
    Vector<Hash256AndMetadata<String>> vectorOfPairs)
  {
    if (filenames.length == 0) {
      BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
      loadHashesAndMetadataFromStreamOrDie(programName, reader, vectorOfPairs);
    } else {
      for (String filename : filenames) {
        loadHashesAndMetadataFromFileOrDie(programName, filename, vectorOfPairs);
      }
    }
  }

  // ----------------------------------------------------------------
  public static Hash256 loadHashFromStream(BufferedReader reader)
    throws IOException, PDQHashFormatException
  {
    String line = reader.readLine();
    if (line == null) {
      return null;
    }
    return Hash256.fromHexString(line);
  }

  // ----------------------------------------------------------------
  public static void loadHashesFromStream(
    BufferedReader reader,
    Vector<Hash256> vectorOfHashes)
      throws IOException, PDQHashFormatException
  {
    while (true) {
      Hash256 hash = loadHashFromStream(reader);
      if (hash == null) {
        break;
      }
      vectorOfHashes.add(hash);
    }
  }

  // ----------------------------------------------------------------
  public static void loadHashesFromFile(
    String filename,
    Vector<Hash256> vectorOfHashes)
      throws IOException, PDQHashFormatException
  {
    BufferedReader reader = new BufferedReader(new FileReader(filename));
    loadHashesFromStream(reader, vectorOfHashes);
    reader.close();
  }

  public static void loadHashesFromFileOrDie(
    String programName,
    String filename,
    Vector<Hash256> vectorOfHashes)
  {
    try {
      loadHashesFromFile(filename, vectorOfHashes);
    } catch (IOException e) {
      System.err.printf("%s: could not read hashes from file \"%s\".\n",
        programName, filename);
      System.exit(1);
    } catch (PDQHashFormatException e) {
      System.err.printf("%s: could not parse hash \"%s\" from file \"%s\".\n",
        programName, e.getUnacceptableInput(), filename);
      System.exit(1);
    }
  }

  // ----------------------------------------------------------------
  public static void loadHashesFromStdin(
    Vector<Hash256> vectorOfHashes)
      throws IOException, PDQHashFormatException
  {
    BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
    loadHashesFromStream(reader, vectorOfHashes);
  }

  public static void loadHashesFromStdinOrDie(
    String programName,
    Vector<Hash256> vectorOfHashes)
  {
    try {
      BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
      loadHashesFromStream(reader, vectorOfHashes);
    } catch (IOException e) {
      System.err.printf("%s: could not read hashes from standard input.\n", programName);
      System.exit(1);
    } catch (PDQHashFormatException e) {
      System.err.printf("%s: could not parse hash \"%s\" from standard input.\n",
        programName, e.getUnacceptableInput());
      System.exit(1);
    }
  }

  // ----------------------------------------------------------------
  public static void loadHashesFromFiles(
    String[] filenames,
    Vector<Hash256> vectorOfHashes)
      throws IOException, PDQHashFormatException
  {
    if (filenames.length == 0) {
      loadHashesFromStdin(vectorOfHashes);
    } else {
      for (String filename : filenames) {
        loadHashesFromFile(filename, vectorOfHashes);
      }
    }
  }

  public static void loadHashesFromFilesOrDie(
    String programName,
    String[] filenames,
    Vector<Hash256> vectorOfHashes)
  {
    if (filenames.length == 0) {
      loadHashesFromStdinOrDie(programName, vectorOfHashes);
    } else {
      for (String filename : filenames) {
        loadHashesFromFileOrDie(programName, filename, vectorOfHashes);
      }
    }
  }
}
