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

export function timeAgo(isoDateString) {
  return formatDistanceToNow(parseISO(isoDateString), {addSuffix: true});
}
