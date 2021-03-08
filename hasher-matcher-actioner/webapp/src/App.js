/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

'use strict';

import React, { useState, useEffect } from 'react';

export default function App() {
  return (
    <>
      <nav class="navbar navbar-expand-md navbar-dark bg-dark">
        <a class="navbar-brand" href="/">Hasher-Matcher-Actioner (HMA)</a>
        <ul class="navbar-nav">
          <li class="nav-item">
            <a class="nav-link" href="/">Dashboard</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="/">Get Metrics</a>
          </li>
          <li class="nav-item">
            <a class="nav-link disabled" href="/">Another Main Menu Item</a>
          </li>
        </ul>
      </nav>
      <main role="main" class="container">
        <div>&nbsp;</div>
        <div class="jumbotron mt-6">
          <h1>HMA Dashboard</h1>
          <p class="lead">Cool metrics:</p>
          <MetricsTable />
        </div>
      </main>
    </>
  );
}

function MetricsTable() {
  const [metrics, setMetrics] = useState(null);
  useEffect(() => {
    fetch("<api-url-goes-here")
    .then(response => response.json())
    .then(
      (metrics) => {
        setMetrics(metrics);
      }
    );
  }, []);
  if (metrics === null || metrics === undefined) {
    return <p>No metrics to display.</p>
  }
  return (
    <table class="table">
      <tbody>
        <tr><td>Metric 1</td><td>{metrics.metric1}</td></tr>
        <tr><td>Metric 2</td><td>{metrics.metric2}</td></tr>
        <tr><td>Metric 3</td><td>{metrics.metric3}</td></tr>
      </tbody>
    </table>
  );
}
