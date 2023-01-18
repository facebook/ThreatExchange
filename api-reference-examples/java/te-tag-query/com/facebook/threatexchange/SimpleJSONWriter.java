// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

package com.facebook.threatexchange;

import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Simple JSON output
 */
public class SimpleJSONWriter {
  LinkedHashMap<String,String> _pairs;

  public SimpleJSONWriter() {
    _pairs = new LinkedHashMap<String,String>();
  }
  public void add(String k, String v) {
    _pairs.put(k, v);
  }
  public void ifValudNotNullAdd(String k, String v) {
    if (v != null) {
      _pairs.put(k, v);
    }
  }
  public void add(String k, int v) {
    _pairs.put(k, Integer.toString(v));
  }
  public String format() {
    StringBuffer sb = new StringBuffer();
    sb.append("{");
    int i = 0;
    for (Map.Entry<String,String> pair : _pairs.entrySet()) {
      String key = pair.getKey();
      String value = pair.getValue();
      // JSON string values are wrapped in double quotes.
      // Any double quotes inside need to be escaped via " -> \".
      // But any *already* escaped \" needs to go to \\\".
      //
      // (This might also be solved by using Jackson or somesuch, but I want
      // to solve this problem without taking a dependency unless I must --
      // dependency complications are the bane of uptake for open-source
      // projects and I want to keep this project simple to install.)
      String escValue = value
        .replace("\\\"", "\001\002\003")
        .replace("\"", "\\\"")
        .replace("\001\002\003", "\\\\\\\"");

      escValue = escValue.replace("\n", "\\n");

      if (i > 0) {
        sb.append(",");
      }
      sb.append("\"").append(key).append("\"");
      sb.append(":");
      sb.append("\"");
      sb.append(escValue);
      sb.append("\"");
      i++;
    }
    sb.append("}");
    return sb.toString();
  }
}
