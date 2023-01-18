/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React from 'react';
import {BrowserRouter as Router, Route, Switch} from 'react-router-dom';
import {AmplifyAuthenticator, AmplifySignIn} from '@aws-amplify/ui-react';

import './styles/_app.scss';

import Sidebar from './Sidebar';
import ContentDetailsSummary from './pages/ContentDetails';
import Matches from './pages/Matches';
import Dashboard from './pages/Dashboard';
import Settings from './pages/Settings';
import SubmitContent from './pages/SubmitContent';
import ContentDetailsWithStepper from './pages/ContentDetailsWithStepper';
import ViewAllBanks from './pages/bank-management/ViewAllBanks';
import ViewBank from './pages/bank-management/ViewBank';
import ViewBankMember from './pages/bank-management/ViewBankMember';
import {AppWithNotifications} from './AppWithNotifications';
import {AppWithConfirmations} from './AppWithConfirmations';
import ViewCollaborations from './pages/collaborations/ViewCollaborations';

export default function App(): JSX.Element {
  return (
    <AmplifyAuthenticator className="container-fluid">
      <div slot="sign-in">
        <AmplifySignIn
          hideSignUp
          headerText="Sign in to Hasher-Matcher-Actioner HMA"
        />
      </div>
      <Router>
        <AppWithNotifications>
          <AppWithConfirmations>
            <div className="row">
              <Sidebar className="col-md-2 bg-light sidebar" />
              <main
                role="main"
                className="col-md-10 px-0 main"
                style={{overflow: 'auto'}}>
                <Switch>
                  <Route path="/matches/:id">
                    <ContentDetailsSummary />
                  </Route>
                  <Route path="/pipeline-progress/:id">
                    <ContentDetailsWithStepper />
                  </Route>
                  <Route path="/matches">
                    <Matches />
                  </Route>
                  <Route path="/submit">
                    <SubmitContent />
                  </Route>
                  <Route path="/settings/:tab?">
                    <Settings />
                  </Route>
                  <Route path="/banks/bank/:bankId/:tab">
                    <ViewBank />
                  </Route>
                  <Route path="/banks/member/:bankMemberId/">
                    <ViewBankMember />
                  </Route>
                  <Route path="/banks/">
                    <ViewAllBanks />
                  </Route>
                  <Route path="/collabs/">
                    <ViewCollaborations />
                  </Route>
                  <Route path="/dashboard/">
                    <Dashboard />
                  </Route>
                  <Route path="/">
                    <SubmitContent />
                  </Route>
                </Switch>
              </main>
            </div>
          </AppWithConfirmations>
        </AppWithNotifications>
      </Router>
    </AmplifyAuthenticator>
  );
}
