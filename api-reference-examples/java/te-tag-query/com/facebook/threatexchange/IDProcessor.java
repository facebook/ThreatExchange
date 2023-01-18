// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

package com.facebook.threatexchange;

import java.util.List;

/**
 * Callback interface for callsites to define what they want to do with each
 * page of threat-descriptor-ID results.
 */
interface IDProcessor {
  public void processIDs(List<String> ids);
}
