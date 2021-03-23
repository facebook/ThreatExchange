/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';
import {BrowserRouter as Router, Route, Link} from 'react-router-dom';
import {AnimatedSwitch} from 'react-router-transition';
import {Auth} from 'aws-amplify';
import {AmplifyAuthenticator, AmplifySignIn} from '@aws-amplify/ui-react';
import Dashboard from './Dashboard';
import MatchDetails from './MatchDetails';
import Matches from './Matches';
import Settings from './Settings';
import Signals from './Signals';
import Upload from './Upload';

export default function App() {
  return (
    <AmplifyAuthenticator>
      <div slot="sign-in">
        <AmplifySignIn
          hideSignUp
          headerText="Sign in to Hasher-Matcher-Actioner HMA"
        />
      </div>
      <Router>
        <nav className="navbar navbar-expand-md navbar-dark bg-dark">
          <a className="navbar-brand" href="/">
            Hasher-Matcher-Actioner (HMA)
          </a>
          <ul className="navbar-nav mr-auto">
            <li className="nav-item">
              <Link to="/" className="nav-link">
                Dashboard
              </Link>
            </li>
            <li className="nav-item">
              <Link to="/matches" className="nav-link">
                Matches
              </Link>
            </li>
            <li className="nav-item">
              <Link to="/signals" className="nav-link">
                Signals
              </Link>
            </li>
            <li className="nav-item">
              <Link to="/upload" className="nav-link">
                Upload
              </Link>
            </li>
          </ul>
          <ul className="navbar-nav">
            <li className="nav-item">
              <Link to="/settings" className="nav-link">
                <span className="glyphicon glyphicon-cog" />
                Settings
              </Link>
            </li>
            <li className="nav-item">
              <a className="nav-link" onClick={() => Auth.signOut()} href="/">
                Sign Out
              </a>
            </li>
          </ul>
        </nav>
        <main role="main" className="container mt-4">
          <AnimatedSwitch
            atEnter={{opacity: 0}}
            atLeave={{opacity: 0}}
            atActive={{opacity: 1}}
            className="switch-wrapper">
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
    </AmplifyAuthenticator>
  );
}
