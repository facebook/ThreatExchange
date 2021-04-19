/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';
import {BrowserRouter as Router, Route, Switch} from 'react-router-dom';
import {AmplifyAuthenticator, AmplifySignIn} from '@aws-amplify/ui-react';

import './styles/_app.scss';

import Sidebar from './Sidebar';
import Dashboard from './Dashboard';
import MatchDetails from './MatchDetails';
import Matches from './pages/Matches';
import Settings from './Settings';
import Signals from './Signals';
import Upload from './Upload';

export default function App() {
  return (
    <AmplifyAuthenticator className="container-fluid">
      <div slot="sign-in">
        <AmplifySignIn
          hideSignUp
          headerText="Sign in to Hasher-Matcher-Actioner HMA"
        />
      </div>
      <Router>
        <div className="row">
          <Sidebar className="col-md-2 bg-light sidebar" />
          <main role="main" className="col-md-10 px-0 main">
            <Switch>
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
            </Switch>
          </main>
        </div>
      </Router>
    </AmplifyAuthenticator>
  );
}
