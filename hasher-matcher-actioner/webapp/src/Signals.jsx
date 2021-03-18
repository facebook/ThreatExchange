/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';

export default function Signals() {
  return (
    <>
      <h1>Signals</h1>
      <div className="row mt-3">
        <div className="col-md-12">
          <div className="card">
            <div className="card-header text-white bg-success">
              <h4 className="mb-0">Signal Source 1</h4>
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
                  <tr>
                    <td>HASH_PDQ</td>
                    <td>12,456</td>
                  </tr>
                  <tr>
                    <td>HASH_PDQ_OCR</td>
                    <td>2,456</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div className="card-footer">
              <small className="font-weight-light">
                as of 12 Mar 2021 2:03pm
              </small>
            </div>
          </div>
        </div>
        <div className="col-md-12 mt-4">
          <div className="card">
            <div className="card-header text-white bg-success">
              <h4 className="mb-0">Signal Source 2</h4>
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
                  <tr>
                    <td>DEBUG_STRING</td>
                    <td>84,823</td>
                  </tr>
                  <tr>
                    <td>HASH_PDQ</td>
                    <td>587</td>
                  </tr>
                  <tr>
                    <td>HASH_PDQ_OCR</td>
                    <td>112</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div className="card-footer">
              <small className="font-weight-light">
                as of 12 Mar 2021 2:03pm
              </small>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
