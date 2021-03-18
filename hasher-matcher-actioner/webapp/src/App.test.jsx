/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';
import {render, screen, test, expect} from '@testing-library/react';
import App from './App';

test('HMA Dashboard', () => {
  render(<App />);
  const dashboardH1 = screen.getByText(/hma dashboard/i);
  expect(dashboardH1).toBeInTheDocument();
});
