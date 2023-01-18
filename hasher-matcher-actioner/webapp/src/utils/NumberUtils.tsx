/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

/**
 * Reduces the width required for displaying a number. eg. 4,000 -> 4k.
 * 2,000,000 -> 2m etc.
 */
export default function shortenNumRepr(n: number): number | string {
  if (n < 1e3) return n;
  if (n >= 1e3 && n < 1e6) return `${+(n / 1e3).toFixed(1)}k`;
  if (n >= 1e6 && n < 1e9) return `${+(n / 1e6).toFixed(1)}m`;
  if (n >= 1e9 && n < 1e12) return `${+(n / 1e9).toFixed(1)}b`;

  return `${+(n / 1e12).toFixed(1)}t`;
}
