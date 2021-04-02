/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */
// TODO I don't like having this but until our js is typed it probably necessary
/* eslint-disable react/prop-types */

import React, {useState, useEffect} from 'react';
import {useHistory} from 'react-router-dom';

import {fetchDashboardSummary} from './Api';

export default function Dashboard() {
  const history = useHistory();
  const [dashboardSummary, setDashboardSummary] = useState(null);

  useEffect(() => {
    fetchDashboardSummary().then(summaries => {
      setDashboardSummary(summaries.dashboard);
    });
  }, []);
  return (
    <>
      <h1>Dashboard</h1>
      <div className="row mt-3">
        <DashboardCard
          title="Hashes"
          details={dashboardSummary ? dashboardSummary.hashes : null}
        />

        <DashboardCard
          title="Matches"
          details={dashboardSummary ? dashboardSummary.matches : null}
          handleOnClick={() => history.push('/matches')}
        />

        <DashboardCard
          title="Actions"
          details={dashboardSummary ? dashboardSummary.actions : null}
        />

        <DashboardCard
          title="Signals"
          details={dashboardSummary ? dashboardSummary.signals : null}
          handleOnClick={() => history.push('/signals')}
        />

        <DashboardCard
          title="System Status"
          details={dashboardSummary ? dashboardSummary.system_status : null}
        />
      </div>
    </>
  );
}

function DashboardCard({title, details, handleOnClick}) {
  return (
    <>
      <div className="col-xl-4 col-lg-4 col-md-6 col-sm-6 col-xs-12 mb-4">
        <div
          className="card text-center"
          role="link"
          onClick={handleOnClick ? () => handleOnClick() : null}
          onKeyDown={e => {
            if (handleOnClick && e.code === 'Enter') {
              handleOnClick();
            }
          }}
          style={handleOnClick ? {cursor: 'pointer'} : {}}
          tabIndex={handleOnClick ? 0 : -1}>
          <div className="card-header text-white bg-success">
            <h4 className="mb-0">{title}</h4>
          </div>

          <DashboardCardBody details={details} />

          <div className="card-footer">
            <small className="font-weight-light">
              as of {details ? details.updated_at : 'unknown'}
            </small>
          </div>
        </div>
      </div>
    </>
  );
}

function DashboardCardBody({details}) {
  if (details) {
    if (details.total && details.today) {
      return (
        <div className="card-body">
          <h5>{details.total.toLocaleString()}</h5>
          <h6>{`${details.today.toLocaleString()} today`}</h6>
        </div>
      );
    }
    if (details.status && details.days_running) {
      return (
        <div className="card-body">
          <h5>{details.status}</h5>
          <h6>{`${details.days_running.toLocaleString()} days`}</h6>
        </div>
      );
    }
  }
  return (
    <div className="card-body">
      <h5>loading... </h5>
    </div>
  );
}
