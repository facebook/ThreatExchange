// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
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
