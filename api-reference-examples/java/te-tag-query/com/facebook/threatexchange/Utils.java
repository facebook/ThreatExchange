// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

package com.facebook.threatexchange;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.PrintStream;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Base64;
import java.util.List;
import java.util.stream.Stream;

/**
 * Utility methods
 */
class Utils {

  /**
   * Supports the paradigm that usage-functions should print to stdout and
   * exit 0 when asked for via --help, and print to stderr and exit 1
   * when unacceptable command-line syntax is encountered.
   */
  public static PrintStream getPrintStream(int exitCode) {
    return exitCode == 0
      ? System.out
      : System.err;
  }

  /**
   * Splits a list of strings into chunks of a given max length.
   * General-purpose, but for this application, intended to satisfy
   * the max-IDs-per-request for the ThreatExchange IDs-to-details URL.
   */
  public static List<List<String>> chunkify(List<String> stringList, int numPerChunk) {
    List<List<String>> chunks = new ArrayList<List<String>>();
    int n = stringList.size();
    String[] stringArray = new String[n];
    int k = 0;
    for (String s : stringList) {
      stringArray[k++] = s;
    }

    for (int i = 0; i < n; i += numPerChunk) {
      int j = i + numPerChunk;
      if (j > n) {
        j = n;
      }
      String[] subArray = Arrays.copyOfRange(stringArray, i, j);
      chunks.add(Arrays.asList(subArray));
    }

    return chunks;
  }

  // Try-catches an annoying should-never-happen unsupported-encoding exception
  public static String urlEncodeUTF8(String input) {
    String retval = null;
    try {
      retval = URLEncoder.encode(input, "UTF-8");
    } catch (java.io.UnsupportedEncodingException e) {
      throw new RuntimeException("Internal coding error in data encoder.\n");
    }
    return retval;
  }

  // Try-catches an annoying should-never-happen unsupported-encoding exception
  public static byte[] getBytesUTF8(String input) {
    byte[] retval = null;
    try {
      retval = input.toString().getBytes("UTF-8");
    } catch (java.io.UnsupportedEncodingException e) {
      throw new RuntimeException("Internal coding error in data encoder.\n");
    }
    return retval;
  }

  public static String td_indicator_typeToFileSuffix(String td_indicator_type) {
    String suffix = ".hsh";
    switch (td_indicator_type) {
    case Constants.INDICATOR_TYPE_PHOTODNA:
      suffix = ".pdna";
      break;
    case Constants.INDICATOR_TYPE_PDQ:
      suffix = ".pdq";
      break;
    case Constants.INDICATOR_TYPE_MD5:
      suffix = ".md5";
      break;
    case Constants.INDICATOR_TYPE_TMK:
      suffix = ".tmk";
      break;
    }
    return suffix;
  }

  public static void outputIndicatorToFile(
    ThreatDescriptor threatDescriptor,
    String path,
    boolean verbose)
      throws FileNotFoundException, IOException
  {
    if (threatDescriptor.td_indicator_type.equals(Constants.INDICATOR_TYPE_TMK)) {
      outputTMKHashToFile(threatDescriptor, path, verbose);
    } else {
      outputNonTMKHashToFile(threatDescriptor, path, verbose);
    }
  }

  // TMK hashes are binary data with data strucure in the TMK package's
  // tmktypes.h. The string attributes are not 8-bit clean in the
  // ThreatExchange API so the td_raw_indicator attribute is stored as base64-encoded,
  // with one caveat: the first 12 bytes (which are ASCII) are stored as
  // such, followed by a pipe delimiter, then the rest of the binary file
  // base64-encdoed. Here we undo that encoding.
  public static void outputTMKHashToFile(
    ThreatDescriptor threatDescriptor,
    String path,
    boolean verbose)
      throws FileNotFoundException, IOException
  {
    FileOutputStream fos = new FileOutputStream(path);
    int hlen = threatDescriptor.td_raw_indicator.length();

    String base64EncodedHash = threatDescriptor.td_raw_indicator;

    byte[] bytes = base64EncodedHash.getBytes();
    byte[] first = Arrays.copyOfRange(bytes, 0, 12);
    byte[] rest = Base64.getDecoder().decode(Arrays.copyOfRange(bytes, 13, hlen));
    fos.write(first);
    fos.write(rest);
    if (verbose) {
      SimpleJSONWriter w = new SimpleJSONWriter();
      w.add("path", path);
      w.add("td_indicator_type", threatDescriptor.td_indicator_type);
      w.add("encoded_length", threatDescriptor.td_raw_indicator.length());
      w.add("binary_length", first.length + rest.length);
      System.out.println(w.format());
      System.out.flush();
    }
    fos.close();
  }

  // Just write PhotoDNA, PDQ, MD5, etc. hash-data to the file contents.
  public static void outputNonTMKHashToFile(
    ThreatDescriptor threatDescriptor,
    String path,
    boolean verbose)
      throws FileNotFoundException, IOException
  {
    FileOutputStream fos = new FileOutputStream(path);

    byte[] bytes = threatDescriptor.td_raw_indicator.getBytes();
    fos.write(bytes);
    if (verbose) {
      SimpleJSONWriter w = new SimpleJSONWriter();
      w.add("path", path);
      w.add("td_indicator", threatDescriptor.td_indicator_type);
      w.add("indicator_length", threatDescriptor.td_raw_indicator.length());
      System.out.println(w.format());
      System.out.flush();
    }

    fos.close();
  }

  // TMK hashes are binary data with data strucure in the TMK package's
  // tmktypes.h. The string attributes are not 8-bit clean in the
  // ThreatExchange API so the td_raw_indicator attribute is stored as base64-encoded,
  // with one caveat: the first 12 bytes (which are ASCII) are stored as
  // such, followed by a pipe delimiter, then the rest of the binary file
  // base64-encdoed. Here we undo that encoding.
  public static String readTMKHashFromFile(String pathAsString, boolean verbose)
    throws FileNotFoundException, IOException
  {
    File file = new java.io.File(pathAsString);
    byte[] binaryContents = Files.readAllBytes(file.toPath());
    int blen = binaryContents.length;
    if (blen < 12) {
      throw new IOException(".tmk file \"" + pathAsString + "\" is too small");
    }

    byte[] binaryFirst = Arrays.copyOfRange(binaryContents, 0, 12);
    byte[] binaryRest = Arrays.copyOfRange(binaryContents, 12, blen);
    byte[] base64Rest = Base64.getEncoder().encode(binaryRest);

    String encoded = (new String(binaryFirst)) + "|" + (new String(base64Rest));

    if (verbose) {
      SimpleJSONWriter w = new SimpleJSONWriter();
      w.add("path", pathAsString);
      w.add("binary_length", blen);
      w.add("encoded_length", encoded.length());
      System.out.println(w.format());
      System.out.flush();
    }
    return encoded;
  }

} // class Utils

