// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

package com.facebook.threatexchange;

import java.io.PrintStream;
import java.util.stream.Stream;

/**
 * Hash-filterer, using hash-text rather than ThreatExchange 'type'
 * field, since it's far more performant to filter on the former
 * than the latter.
 */
class HashFiltererFactory {
  private static final String OPTION_PHOTODNA = "photodna";
  private static final String OPTION_PDQ      = "pdq";
  private static final String OPTION_MD5      = "md5";
  private static final String OPTION_TMK      = "tmk";
  private static final String OPTION_ALL      = "all";

  public static void list(PrintStream o) {
    o.printf("Hash-type filters:\n");
    o.printf("  %s\n", OPTION_PHOTODNA);
    o.printf("  %s\n", OPTION_PDQ);
    o.printf("  %s\n", OPTION_MD5);
    o.printf("  %s\n", OPTION_TMK);
    o.printf("  %s\n", OPTION_ALL);
  }

  public static HashFilterer create(String name) {
    if (name.equals(OPTION_PHOTODNA)) {
      return new PhotoDNAHashFilterer();
    } else if (name.equals(OPTION_PDQ)) {
      return new PDQHashFilterer();
    } else if (name.equals(OPTION_MD5)) {
      return new MD5HashFilterer();
    } else if (name.equals(OPTION_TMK)) {
      return new TMKHashFilterer();
    } else if (name.equals(OPTION_ALL)) {
      return new AllHashFilterer();
    } else {
      return null;
    }
  }
}

interface HashFilterer {
  public abstract boolean accept(String hash);
  public abstract String getTEName();
}

/**
 * Filters for any hash-type
 */
class AllHashFilterer implements HashFilterer {
  @Override
  public boolean accept(String hash) {
    return true;
  }
  @Override
  public String getTEName() {
    return null;
  }
}

/**
 * Filters ideally for comma-delimited decimal, 144 slots.
 * Only does the minimal check to differentiate from other hash-types
 * we support.
 */
class PhotoDNAHashFilterer implements HashFilterer {
  @Override
  public boolean accept(String hash) {
    if (hash.length() < 287) { // Shortest: 0,0,0,...,0,0,0
      return false;
    }
    return true;
  }
  @Override
  public String getTEName() {
    return "HASH_PHOTODNA";
  }
}

/**
 * Filters ideally for 64 hex digits.
 * Only does the minimal check to differentiate from other hash-types
 * we support.
 */
class PDQHashFilterer implements HashFilterer {
  @Override
  public boolean accept(String hash) {
    if (hash.length() != 64) {
      return false;
    }
    return true;
  }
  @Override
  public String getTEName() {
    return "HASH_PDQ";
  }
}

/**
 * Filters ideally for 32 hex digits
 * Only does the minimal check to differentiate from other hash-types
 * we support.
 */
class MD5HashFilterer implements HashFilterer {
  @Override
  public boolean accept(String hash) {
    if (hash.length() != 32) {
      return false;
    }
    return true;
  }
  @Override
  public String getTEName() {
    return "HASH_MD5";
  }
}

/**
 * Filters ideally for very long (256KB-ish)
 * Only does the minimal check to differentiate from other hash-types
 * we support.
 */
class TMKHashFilterer implements HashFilterer {
  @Override
  public boolean accept(String hash) {
    return hash.length() >= 100000;
  }
  @Override
  public String getTEName() {
    return "HASH_TMK";
  }
}

