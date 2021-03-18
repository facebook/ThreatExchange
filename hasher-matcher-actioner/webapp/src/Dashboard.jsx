/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';
import {useHistory} from 'react-router-dom';

export default function Dashboard() {
  const history = useHistory();
  return (
    <>
      <h1>Dashboard</h1>
      <div className="row mt-3">
        <div className="col-xl-4 col-lg-4 col-md-6 col-sm-6 col-xs-12 mb-4">
          <div className="card text-center">
            <div className="card-header text-white bg-success">
              <h4 className="mb-0">Hashes</h4>
            </div>
            <div className="card-body">
              <h5>34,217,123,456</h5>
              <h6>145,609,278 today</h6>
            </div>
            <div className="card-footer">
              <small className="font-weight-light">
                as of 12 Mar 2021 2:03pm
              </small>
            </div>
          </div>
        </div>
        <div className="col-xl-4 col-lg-4 col-md-6 col-sm-6 col-xs-12 mb-4">
          <div
            className="card text-center"
            role="link"
            onClick={() => history.push('/matches')}
            onKeyDown={e => {
              if (e.code === 'Enter') {
                history.push('/matches');
              }
            }}
            style={{cursor: 'pointer'}}
            tabIndex={0}>
            <div className="card-header text-white bg-success">
              <h4 className="mb-0">Matches</h4>
            </div>
            <div className="card-body">
              <h5>14,376</h5>
              <h6>109 today</h6>
            </div>
            <div className="card-footer">
              <small className="font-weight-light">
                last match 12 Mar 2021 11:03am
              </small>
            </div>
          </div>
        </div>
        <div className="col-xl-4 col-lg-4 col-md-6 col-sm-6 col-xs-12 mb-4">
          <div className="card text-center">
            <div className="card-header text-white bg-success">
              <h4 className="mb-0">Actions</h4>
            </div>
            <div className="card-body">
              <h5>3,456</h5>
              <h6>27 today</h6>
            </div>
            <div className="card-footer">
              <small className="font-weight-light">
                as of 12 Mar 2021 2:03pm
              </small>
            </div>
          </div>
        </div>
        <div className="col-xl-4 col-lg-4 col-md-6 col-sm-6 col-xs-12 mb-4">
          <div
            className="card text-center"
            role="link"
            onClick={() => history.push('/signals')}
            onKeyDown={e => {
              if (e.code === 'Enter') {
                history.push('/signals');
              }
            }}
            style={{cursor: 'pointer'}}
            tabIndex={0}>
            <div className="card-header text-white bg-success">
              <h4 className="mb-0">Signals</h4>
            </div>
            <div className="card-body">
              <h5>123,456</h5>
              <h6>654 today</h6>
            </div>
            <div className="card-footer">
              <small className="font-weight-light">
                as of 12 Mar 2021 2:03pm
              </small>
            </div>
          </div>
        </div>
        <div className="col-xl-4 col-lg-4 col-md-6 col-sm-6 col-xs-12 mb-4">
          <div className="card text-center">
            <div className="card-header text-white bg-success">
              <h4 className="mb-0">System Status</h4>
            </div>
            <div className="card-body">
              <h5>Running</h5>
              <h6>47 days</h6>
            </div>
            <div className="card-footer">
              <small className="font-weight-light">
                running since 7 Feb 2021
              </small>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
