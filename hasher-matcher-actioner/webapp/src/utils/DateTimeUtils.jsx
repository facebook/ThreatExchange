/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import {formatDistanceToNow, parseISO} from 'date-fns';

export function formatTimestamp(timestamp) {
  if (!timestamp) {
    return 'Unknown';
  }
  return new Intl.DateTimeFormat('default', {
    day: 'numeric',
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(new Date(timestamp));
}

/**
 * Convert an ISO Date String to a relative time value.
 * eg. Converts 2021-08-28T00:00:00 into 12 minutes ago.
 *
 * @param {string} isoDateString
 * @returns string
 */
export function timeAgo(isoDateString) {
  return formatDistanceToNow(parseISO(isoDateString), {addSuffix: true});
}
