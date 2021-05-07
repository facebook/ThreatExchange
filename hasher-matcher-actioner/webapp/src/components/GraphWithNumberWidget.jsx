/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';
import PropTypes from 'prop-types';

// import uPlot from 'uplot';
import UplotReact from 'uplot-react';
import '../../node_modules/uplot/dist/uPlot.min.css';

/**
 * Reduces the width required for displaying a number. eg. 4,000 -> 4k.
 * 2,000,000 -> 2m etc.
 */
function shortenNumRepr(n) {
  if (n < 1e3) return n;
  if (n >= 1e3 && n < 1e6) return `${+(n / 1e3).toFixed(1)}k`;
  if (n >= 1e6 && n < 1e9) return `${+(n / 1e6).toFixed(1)}m`;
  if (n >= 1e9 && n < 1e12) return `${+(n / 1e9).toFixed(1)}b`;

  return `${+(n / 1e12).toFixed(1)}t`;
}

const opts = {
  id: 'chart1',
  class: 'my-chart',
  width: 500,
  height: 200,
  axes: [
    {},
    {
      values: (_, vals) => vals.map(shortenNumRepr),
      space: 20,
    },
  ],
  series: [
    {},
    {
      stroke: 'rgba(5, 141, 199, 1)',
      fill: 'rgba(255, 0, 0, 0.3)',
    },
  ],
};

export default function GraphWithNumberWidget({graphData}) {
  return (
    <div>
      <UplotReact options={opts} data={graphData} />
    </div>
  );
}

GraphWithNumberWidget.propTypes = {
  graphData: PropTypes.arrayOf(PropTypes.number).isRequired,
};
