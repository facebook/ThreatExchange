/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';
import { BrowserRouter as Router, Route, Link } from 'react-router-dom';
import { AnimatedSwitch } from 'react-router-transition';
import Dashboard from './Dashboard';
import MatchDetails from './MatchDetails';
import Matches from './Matches';
import Settings from './Settings';
import Signals from './Signals';
import Upload from './Upload';

export default function App() {
  return (
    <Router>
      <nav class="navbar navbar-expand-md navbar-dark bg-dark">
        <a class="navbar-brand" href="/">Hasher-Matcher-Actioner (HMA)</a>
        <ul class="navbar-nav mr-auto">
          <li class="nav-item">
            <Link to="/" className="nav-link">Dashboard</Link>
          </li>
          <li class="nav-item">
            <Link to="/matches" className="nav-link">Matches</Link>
          </li>
          <li class="nav-item">
            <Link to="/signals" className="nav-link">Signals</Link>
          </li>
          <li class="nav-item">
            <Link to="/upload" className="nav-link">Upload</Link>
          </li>
        </ul>
        <ul class="navbar-nav">
          <li class="nav-item">
            <Link to="/settings" className="nav-link"><span class="glyphicon glyphicon-cog"></span>Settings</Link>
          </li>
        </ul>
      </nav>
      <main role="main" class="container mt-4">
        <AnimatedSwitch
          atEnter={{ opacity: 0 }}
          atLeave={{ opacity: 0 }}
          atActive={{ opacity: 1 }}
          className="switch-wrapper"
          >
          <Route path="/matches/:id">
            <MatchDetails />
          </Route>
          <Route path="/matches">
            <Matches />
          </Route>
          <Route path="/signals">
            <Signals />
          </Route>
          <Route path="/upload">
            <Upload />
          </Route>
          <Route path="/settings">
            <Settings />
          </Route>
          <Route path="/">
            <Dashboard />
          </Route>
        </AnimatedSwitch>
      </main>
    </Router>
  );
}
