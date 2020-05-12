// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

package com.facebook.threatexchange;

import java.io.PrintStream;
import java.util.stream.Stream;

/**
 * Indicator-type filterer, using indicator-text rather than ThreatExchange
 * 'type' field since it's far more performant to filter on the former than
 * the latter.
 */
class IndicatorTypeFiltererFactory {
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

  public static IndicatorTypeFilterer create(String name) {
    if (name.equals(OPTION_PHOTODNA)) {
      return new PhotoDNAIndicatorTypeFilterer();
    } else if (name.equals(OPTION_PDQ)) {
      return new PDQIndicatorTypeFilterer();
    } else if (name.equals(OPTION_MD5)) {
      return new MD5IndicatorTypeFilterer();
    } else if (name.equals(OPTION_TMK)) {
      return new TMKIndicatorTypeFilterer();
    } else if (name.equals(OPTION_ALL)) {
      return new AllIndicatorTypeFilterer();
    } else {
      return null;
    }
  }
}

interface IndicatorTypeFilterer {
  public abstract boolean accept(String indicatorText);
  public abstract String getTEName();
}

/**
 * Filters for any indicator-type
 */
class AllIndicatorTypeFilterer implements IndicatorTypeFilterer {
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
 * we care about.
 */
class PhotoDNAIndicatorTypeFilterer implements IndicatorTypeFilterer {
  @Override
  public boolean accept(String indicator) {
    if (indicator.length() < 287) { // Shortest: 0,0,0,...,0,0,0
      return false;
    }
    if (indicator.length() > 575) { // Longest: 255,255,...,255,255
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
 * we care care about.
 */
class PDQIndicatorTypeFilterer implements IndicatorTypeFilterer {
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
 * we care about.
 */
class MD5IndicatorTypeFilterer implements IndicatorTypeFilterer {
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
 * we care about.
 */
class TMKIndicatorTypeFilterer implements IndicatorTypeFilterer {
  @Override
  public boolean accept(String indicator) {
    return indicator.length() >= 100000;
  }
  @Override
  public String getTEName() {
    return "HASH_TMK";
  }
}

