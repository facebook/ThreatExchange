/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import 'bootstrap/dist/css/bootstrap.min.css';

import React from 'react';
import ReactDOM from 'react-dom';
import Amplify from 'aws-amplify';
import App from './App';

Amplify.configure({
  Auth: {
    // Amazon Region of the Cognito user pool
    region: process.env.REACT_APP_REGION,

    // Amazon Cognito user pool id
    userPoolId: process.env.REACT_APP_USER_POOL_ID,

    // Amazon Cognito user pool app client id (26-char alphanumeric string)
    userPoolWebClientId: process.env.REACT_APP_USER_POOL_APP_CLIENT_ID,
  },
  API: {
    endpoints: [
      {
        name: 'hma_api',
        endpoint: process.env.REACT_APP_HMA_API_ENDPOINT,
      },
    ],
  },
});

ReactDOM.render(<App />, document.getElementById('root'));
