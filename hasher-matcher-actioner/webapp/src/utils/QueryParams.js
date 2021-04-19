/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

/* eslint-disable import/prefer-default-export */
/* This module will have other utility functions. The default export does not
 * make sense here.
 */

import {useLocation} from 'react-router-dom';

export function useQuery() {
  return new URLSearchParams(useLocation().search);
}
