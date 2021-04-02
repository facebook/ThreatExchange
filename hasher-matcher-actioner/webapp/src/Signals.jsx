/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */
// TODO I don't like having this but until our js is typed it probably necessary
/* eslint-disable react/prop-types */

import React, {useState, useEffect} from 'react';
import Spinner from 'react-bootstrap/Spinner';
import {Collapse} from 'react-bootstrap';

import {fetchSignalSummary} from './Api';

export default function Signals() {
  const [signalSummary, setSignalSummary] = useState(null);

  useEffect(() => {
    fetchSignalSummary().then(summaries => {
      setSignalSummary(summaries.signals);
    });
  }, []);

  return (
    <>
      <h1>Signals</h1>
      <div className="row mt-3">
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
                  <SignalSummary summary={summary} />
                ))
              : null}
          </>
        </Collapse>
      </div>
    </>
  );
}

function SignalSummary({summary}) {
  return (
    <>
      <div className="col-md-12 mb-4">
        <div className="card">
          <div className="card-header text-white bg-success">
            <h4 className="mb-0">{summary.name}</h4>
          </div>
          <div className="card-body">
            <table className="table mb-0">
              <thead>
                <tr>
                  <th>Signal Type</th>
                  <th>Number of Signals</th>
                </tr>
              </thead>
              <tbody>
                {summary.signals !== null && summary.signals.length ? (
                  summary.signals.map(signal => (
                    <tr>
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
            </table>
          </div>
          <div className="card-footer">
            <small className="font-weight-light">
              as of {summary.updated_at}
            </small>
          </div>
        </div>
      </div>
    </>
  );
}
