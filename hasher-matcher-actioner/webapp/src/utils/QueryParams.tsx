/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

/* eslint-disable import/prefer-default-export */
/* This module will have other utility functions. The default export does not
 * make sense here.
 */

import {useLocation} from 'react-router-dom';

export function useQuery(): URLSearchParams {
  return new URLSearchParams(useLocation().search);
}
