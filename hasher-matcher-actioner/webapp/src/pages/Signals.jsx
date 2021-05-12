/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */
// TODO I don't like having this but until our js is typed it probably necessary
/* eslint-disable react/prop-types */

import React, {useState, useEffect} from 'react';
import Spinner from 'react-bootstrap/Spinner';
import {Collapse, Row, Col, Card, Table} from 'react-bootstrap';
import FixedWidthCenterAlignedLayout from './layouts/FixedWidthCenterAlignedLayout';

import {fetchSignalSummary} from '../Api';

export default function Signals() {
  const [signalSummary, setSignalSummary] = useState(null);

  useEffect(() => {
    fetchSignalSummary().then(summaries => {
      // TODO this will spin forever if no signals are found (fix: should add second Collapse)
      if (summaries.signals.length) {
        setSignalSummary(summaries.signals);
      }
    });
  }, []);

  return (
    <FixedWidthCenterAlignedLayout title="Signals">
      <Row className="mt-3">
        <Spinner
          hidden={signalSummary !== null}
          animation="border"
          role="status">
          <span className="sr-only">Loading...</span>
        </Spinner>
        <Collapse in={signalSummary !== null}>
          <>
            {signalSummary !== null && signalSummary.length
              ? signalSummary.map(summary => (
                  <SignalSummary key={summary.name} summary={summary} />
                ))
              : null}
          </>
        </Collapse>
      </Row>
    </FixedWidthCenterAlignedLayout>
  );
}

function SignalSummary({summary}) {
  return (
    <Col key={summary.name} md="12" className="mb-4">
      <Card>
        <Card.Header as="h4" className="text-white bg-primary">
          Dataset: {summary.name}
        </Card.Header>
        <Card.Body className="py-0">
          <Table className="mb-0">
            <thead>
              <tr>
                <th>Signal Type</th>
                <th>Number of Signals</th>
              </tr>
            </thead>
            <tbody>
              {summary.signals !== null && summary.signals.length ? (
                summary.signals.map(signal => (
                  <tr key={signal}>
                    <td>{signal.type}</td>
                    <td>{signal.count}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5}>No Signals Found.</td>
                </tr>
              )}
            </tbody>
          </Table>
        </Card.Body>
        <Card.Footer as="small" className="font-weight-light">
          as of {summary.updated_at}
        </Card.Footer>
      </Card>
    </Col>
  );
}
