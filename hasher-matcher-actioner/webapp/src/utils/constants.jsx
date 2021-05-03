/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

// Matchtes OpinionString in hmalib/lambdas/api/matches.py
export const OPINION_STRING = Object.freeze({
  TRUE_POSITIVE: 'True Positive',
  FALSE_POSITIVE: 'False Positive',
  UKNOWN: 'Unknown',
  DISPUTED: 'Disputed',
});

// Matchtes PendingOpinionChange in hmalib/common/signal_models.py
export const PENDING_OPINION_CHANGE = Object.freeze({
  MARK_TRUE_POSITIVE: 'mark_true_positive',
  MARK_FALSE_POSITIVE: 'mark_false_positive',
  REMOVE_OPINION: 'remove_opinion',
  NONE: 'none',
});

export const SUBMISSION_TYPE = Object.freeze({
  UPLOAD: 'Direct Upload',
  RAW: 'Raw Value (example only)',
  S3_OBJECT: 'S3 Object (example only)',
  URL: 'URL (example only)',
});
