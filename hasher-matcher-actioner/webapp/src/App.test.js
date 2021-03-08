/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

'use strict';

import { render, screen } from '@testing-library/react';
import App from './App';

test('HMA Dashboard', () => {
  render(<App />);
  const dashboardH1 = screen.getByText(/hma dashboard/i);
  expect(dashboardH1).toBeInTheDocument();
});
