/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';
import PropTypes from 'prop-types';

// import uPlot from 'uplot';
import UplotReact from 'uplot-react';
import '../../node_modules/uplot/dist/uPlot.min.css';
import shortenNumRepr from '../utils/NumberUtils';

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
