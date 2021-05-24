/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';
import {
  BrowserRouter as Router,
  Redirect,
  Route,
  Switch,
} from 'react-router-dom';
import {AmplifyAuthenticator, AmplifySignIn} from '@aws-amplify/ui-react';

import './styles/_app.scss';

import Sidebar from './Sidebar';
import ContentDetails from './pages/ContentDetails';
import Matches from './pages/Matches';
import Dashboard from './pages/Dashboard';
import Settings from './pages/Settings';
import Upload from './Upload';
import SubmitContent from './pages/SubmitContent';

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
          <main
            role="main"
            className="col-md-10 px-0 main"
            style={{overflow: 'auto'}}>
            <Switch>
              <Route path="/matches/:id">
                <ContentDetails />
              </Route>
              <Route path="/matches">
                <Matches />
              </Route>
              <Route path="/upload">
                <Upload />
              </Route>
              <Route path="/submit">
                <SubmitContent />
              </Route>
              <Route path="/settings/:tab">
                <Settings />
              </Route>
              <Route path="/settings">
                <Redirect to="/settings/signals" />
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
