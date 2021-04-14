/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */
// TODO I don't like having this but until our js is typed it probably necessary
/* eslint-disable react/prop-types */

import React, {useState, useEffect} from 'react';
import {useHistory} from 'react-router-dom';
import {Col, Card, Row} from 'react-bootstrap';

import {fetchDashboardCardSummary} from './Api';

export default function Dashboard() {
  const history = useHistory();

  return (
    <>
      <h1>Dashboard</h1>
      <Row className="mt-3">
        <DashboardCard title="Hashes" endpoint="dashboard-hashes" />

        <DashboardCard
          title="Matches"
          endpoint="dashboard-matches"
          handleOnClick={() => history.push('/matches')}
        />

        <DashboardCard title="Actions" endpoint="dashboard-actions" />

        <DashboardCard
          title="Signals"
          endpoint="dashboard-signals"
          handleOnClick={() => history.push('/signals')}
        />

        <DashboardCard title="System Status" endpoint="dashboard-status" />
      </Row>
    </>
  );
}

function DashboardCard({title, endpoint, handleOnClick}) {
  const [details, setDetails] = useState(null);

  useEffect(() => {
    fetchDashboardCardSummary(endpoint).then(summaries => {
      setDetails(summaries[endpoint]);
    });
  }, []);
  return (
    <>
      <Col xl="4" lg="4" md="6" sm="6" xs="12" className="mb-4">
        <Card
          className="text-center"
          role="link"
          onClick={handleOnClick ? () => handleOnClick() : null}
          onKeyDown={e => {
            if (handleOnClick && e.code === 'Enter') {
              handleOnClick();
            }
          }}
          style={handleOnClick ? {cursor: 'pointer'} : {}}
          tabIndex={handleOnClick ? 0 : -1}>
          <Card.Header as="h4" className="text-white bg-primary">
            {title}
          </Card.Header>

          <DashboardCardBody details={details} />

          <Card.Footer as="small" className="font-weight-light">
            as of {details ? details.updated_at : 'unknown'}
          </Card.Footer>
        </Card>
      </Col>
    </>
  );
}

function DashboardCardBody({details}) {
  if (details) {
    if (details.total != null && details.today != null) {
      return (
        <Card.Body>
          <h5>{details.total.toLocaleString()}</h5>
          <h6>{`${details.today.toLocaleString()} today`}</h6>
        </Card.Body>
      );
    }
    if (details.status != null && details.days_running != null) {
      return (
        <Card.Body>
          <h5>{details.status}</h5>
          <h6>{`${details.days_running.toLocaleString()} days`}</h6>
        </Card.Body>
      );
    }
  }
  return <Card.Body as="h5">loading...</Card.Body>;
}
