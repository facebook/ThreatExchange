/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 *
 * TODO: typescript supports enums. However, all files that use enums from here
 * need to be converted to typescript before we can change this file into
 * typescript.
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

// Corseponds  SubmissionType in hmalib/api/submit.py
export const SUBMISSION_TYPE = Object.freeze({
  POST_URL_UPLOAD: 'Upload',
  FROM_URL: 'From URL',
});

// Matchtes MetricTimePeriod in hmalib/metrics/query.py
export const StatsTimeSpans = Object.freeze({
  HOURS_1: '1h',
  HOURS_24: '24h',
  DAYS_7: '7d',
});

// Matchtes stat_name_to_metric in hmalib/lambdas/api/stats.py
export const StatNames = Object.freeze({
  HASHES: 'hashes',
  MATCHES: 'matches',
});

// Matches threatexchange.content_type.* for each subclass of ContentType, get_name()
// >>> from threatexchange.content_type.meta import get_all_content_types
// >>> [content_type.get_name() for content_type in get_all_content_types()]
export const ContentType = Object.freeze({
  PHOTO: 'photo',
  TEXT: 'text',
  VIDEO: 'video',
});
