/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState, useCallback} from 'react';
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
      stroke: 'rgba(134, 182, 254, 1)',
      fill: 'rgba(134, 182, 254, 0.3)',
    },
  ],
};

export default function GraphWithNumberWidget({graphData}) {
  // Uses https://reactjs.org/docs/hooks-faq.html#how-can-i-measure-a-dom-node
  //  to resize the graph on first render and on resizes
  const [width, setWidth] = useState(0);

  const measuredRef = useCallback(node => {
    if (node !== null) {
      setWidth(node.getBoundingClientRect().width);
    }
  }, []);

  const myOpts = {...opts, width};

  return (
    <div ref={measuredRef}>
      <UplotReact options={myOpts} data={graphData} />
    </div>
  );
}

GraphWithNumberWidget.propTypes = {
  graphData: PropTypes.arrayOf(PropTypes.number).isRequired,
};
