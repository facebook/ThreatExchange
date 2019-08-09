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
  public void add(String k, int v) {
    _pairs.put(k, Integer.toString(v));
  }
  public String format() {
    StringBuffer sb = new StringBuffer();
    sb.append("{");
    int i = 0;
    for (Map.Entry<String,String> pair : _pairs.entrySet()) {
      if (i > 0) {
        sb.append(",");
      }
      sb.append("\"").append(pair.getKey()).append("\"");
      sb.append(":");
      sb.append("\"").append(pair.getValue()).append("\"");
      i++;
    }
    sb.append("}");
    return sb.toString();
  }
}
