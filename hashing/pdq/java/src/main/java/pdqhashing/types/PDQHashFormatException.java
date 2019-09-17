// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

package pdqhashing.types;

public class PDQHashFormatException extends Exception {
  private final String _unacceptableInput;
  PDQHashFormatException(String unacceptableInput) {
    _unacceptableInput = unacceptableInput;
  }
  public String getUnacceptableInput() {
    return _unacceptableInput;
  }
}
