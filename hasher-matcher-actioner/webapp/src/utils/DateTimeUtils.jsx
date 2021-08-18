/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 * the timestamps passed to this file originate from python however
 * https://stackoverflow.com/questions/19654578/python-utc-datetime-objects-iso-format-doesnt-include-z-zulu-or-zero-offset
 *  so we ~hack-ly add a Z to the isoDateStrings
 */

import {formatDistanceToNow, parseISO, isToday, format} from 'date-fns';

export function toDate(isoDateString) {
  return parseISO(`${isoDateString}Z`);
}

export function formatTimestamp(isoDateString) {
  if (!isoDateString) {
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
    timeZoneName: 'short',
  }).format(parseISO(`${isoDateString}Z`));
}

/**
 * Convert an ISO Date String to a relative time value.
 * eg. Converts 2021-08-28T00:00:00 into 12 minutes ago.
 *
 * @param {string} isoDateString
 * @returns string
 */
export function timeAgo(isoDateString) {
  return formatDistanceToNow(parseISO(`${isoDateString}Z`), {
    addSuffix: true,
  });
}

/**
 * If date is of today, return an hh:mm:ss AM/PM style. If not, return a fuller
 * string.
 */
export function timeOnlyIfToday(date) {
  if (isToday(date)) {
    return format(date, 'pp');
  }
  return format(date, 'PPpp');
}
