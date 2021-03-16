/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';

export default function Signals() {
  return (
    <>
      <h1>Signals</h1>
      <div class="row mt-3">
        <div class="col-md-12">
          <div class="card">
            <div class="card-header text-white bg-success"><h4 class="mb-0">Signal Source 1</h4></div>
            <div class="card-body">
              <table class="table mb-0">
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
            <div class="card-footer"><small class="font-weight-light">as of 12 Mar 2021 2:03pm</small></div>
          </div>
        </div>
        <div class="col-md-12 mt-4">
          <div class="card">
            <div class="card-header text-white bg-success"><h4 class="mb-0">Signal Source 2</h4></div>
            <div class="card-body">
              <table class="table mb-0">
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
            <div class="card-footer"><small class="font-weight-light">as of 12 Mar 2021 2:03pm</small></div>
          </div>
        </div>
      </div>
    </>
  );
}
