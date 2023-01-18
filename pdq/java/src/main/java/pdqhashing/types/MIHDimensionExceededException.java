// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

package pdqhashing.types;

public class MIHDimensionExceededException extends Exception {
  private final String _errorMessage;
  public MIHDimensionExceededException(String errorMessage) {
    _errorMessage = errorMessage;
  }
  public String getErrorMessage() {
    return _errorMessage;
  }
}
