package com.facebook.threatexchange;

import java.io.PrintStream;
import java.net.URL;
import java.net.URLEncoder;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Stream;

// ================================================================
// UTILITY METHODS
// ================================================================

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
      System.err.printf("Internal coding error in data encoder.\n");
      System.exit(1);
    }
    return retval;
  }

  // Try-catches an annoying should-never-happen unsupported-encoding exception
  public static byte[] getBytesUTF8(String input) {
    byte[] retval = null;
    try {
      retval = input.toString().getBytes("UTF-8");
    } catch (java.io.UnsupportedEncodingException e) {
      System.err.printf("Internal coding error in data encoder.\n");
      System.exit(1);
    }
    return retval;
  }

} // class Utils

