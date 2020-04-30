// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

package com.facebook.threatexchange;

import java.io.PrintStream;
import java.util.stream.Stream;

/**
 * Descriptor-filterer, using indicator-text rather than ThreatExchange 'type'
 * field, since it's far more performant to filter on the former than the
 * latter.
 */
class DescriptorFiltererFactory {
  private static final String OPTION_PHOTODNA = "photodna";
  private static final String OPTION_PDQ      = "pdq";
  private static final String OPTION_MD5      = "md5";
  private static final String OPTION_TMK      = "tmk";
  private static final String OPTION_ALL      = "all";

  public static void list(PrintStream o) {
    o.printf("Indicator-type filters:\n");
    o.printf("  %s\n", OPTION_PHOTODNA);
    o.printf("  %s\n", OPTION_PDQ);
    o.printf("  %s\n", OPTION_MD5);
    o.printf("  %s\n", OPTION_TMK);
    o.printf("  %s\n", OPTION_ALL);
  }

  public static DescriptorFilterer create(String name) {
    if (name.equals(OPTION_PHOTODNA)) {
      return new PhotoDNADescriptorFilterer();
    } else if (name.equals(OPTION_PDQ)) {
      return new PDQDescriptorFilterer();
    } else if (name.equals(OPTION_MD5)) {
      return new MD5DescriptorFilterer();
    } else if (name.equals(OPTION_TMK)) {
      return new TMKDescriptorFilterer();
    } else if (name.equals(OPTION_ALL)) {
      return new AllDescriptorFilterer();
    } else {
      return null;
    }
  }
}

interface DescriptorFilterer {
  public abstract boolean accept(String indicatorText);
  public abstract String getTEName();
}

/**
 * Filters for any indicator-type
 */
class AllDescriptorFilterer implements DescriptorFilterer {
  @Override
  public boolean accept(String indicatorType) {
    return true;
  }
  @Override
  public String getTEName() {
    return null;
  }
}

/**
 * Filters ideally for comma-delimited decimal, 144 slots.
 * Only does the minimal check to differentiate from other indicator-types
 * we support.
 */
class PhotoDNADescriptorFilterer implements DescriptorFilterer {
  @Override
  public boolean accept(String indicator) {
    if (indicator.length() < 287) { // Shortest: 0,0,0,...,0,0,0
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
 * Only does the minimal check to differentiate from other indicator-types
 * we support.
 */
class PDQDescriptorFilterer implements DescriptorFilterer {
  @Override
  public boolean accept(String indicator) {
    if (indicator.length() != 64) {
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
 * Only does the minimal check to differentiate from other indicator-types
 * we support.
 */
class MD5DescriptorFilterer implements DescriptorFilterer {
  @Override
  public boolean accept(String indicator) {
    if (indicator.length() != 32) {
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
 * Only does the minimal check to differentiate from other indicator-types
 * we support.
 */
class TMKDescriptorFilterer implements DescriptorFilterer {
  @Override
  public boolean accept(String indicator) {
    return indicator.length() >= 100000;
  }
  @Override
  public String getTEName() {
    return "HASH_TMK";
  }
}

