/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';
import Tabs from 'react-bootstrap/Tabs';
import Tab from 'react-bootstrap/Tab';

export default function Settings() {
  return (
    <>
      <Tabs defaultActiveKey="signals" id="setting-tabs">
        <Tab eventKey="signals" title="Signals">
          <h2>Datasets</h2>
          <div className="row mt-3">
            <div className="col-xl-4 col-lg-4 col-md-6 col-sm-6 col-xs-12 mb-4">
              <div className="card text-center">
                <div className="card-header text-white bg-success">
                  <h4 className="mb-0">Collaboration on Cat Imagery</h4>
                </div>
                <h6 className="card-subtitle mt-0 mb-0 text-muted">Shared</h6>
                <div className="card-body text-left">
                  <p className="card-text">
                    <h5>Enabled</h5>
                    <h5>Labels</h5>
                    <ul>
                      <li>cat</li>
                      <li>unverified</li>
                      <li>*low_precision</li>
                    </ul>
                    <h5>Matching</h5>
                    <ul>
                      <li>PDQ: Distance 17</li>
                    </ul>
                  </p>
                </div>
                <ul className="list-group list-group-flush text-left">
                  <li className="list-group-item">
                    <h5>Source: ThreatExchange Cat Dataset</h5>
                    <h6>Label Map</h6>
                    <ul>
                      <li>low_precision ={'>'} *</li>
                    </ul>
                  </li>
                </ul>
                <a href="#todo" className="btn btn-primary">
                  Edit
                </a>
              </div>
            </div>
            <div className="col-xl-4 col-lg-4 col-md-6 col-sm-6 col-xs-12 mb-4">
              <div className="card text-center">
                <div className="card-header text-white bg-success">
                  <h4 className="mb-0">Verified Cat Imagery</h4>
                </div>
                <h6 className="card-subtitle mt-0 mb-0 text-muted">Shared</h6>
                <div className="card-body text-left">
                  <p className="card-text">
                    <h5>Enabled</h5>
                    <h5>Labels</h5>
                    <ul>
                      <li>cat</li>
                      <li>delete</li>
                    </ul>
                    <h5>Matching</h5>
                    <ul>
                      <li>PDQ: Distance 31</li>
                    </ul>
                    <h5>Share To</h5>
                    <ul>
                      <li>ThreatExchange Cat Dataset</li>
                    </ul>
                  </p>
                </div>
                <ul className="list-group list-group-flush text-left">
                  <li className="list-group-item">
                    <h5>Share To: ThreatExchange Cat Dataset</h5>
                    <h6>Labels</h6>
                    <ul>
                      <li>cat</li>
                    </ul>
                  </li>
                </ul>
                <a href="#todo" className="btn btn-primary">
                  Edit
                </a>
              </div>
            </div>
            <div className="col-xl-4 col-lg-4 col-md-6 col-sm-6 col-xs-12 mb-4">
              <div className="card text-center">
                <div className="card-header text-white bg-success">
                  <h4 className="mb-0">Dog Media</h4>
                </div>
                <div className="card-body text-left">
                  <p className="card-text">
                    <h5>Enabled</h5>
                    <h5>Labels</h5>
                    <ul>
                      <li>dog</li>
                      <li>review</li>
                    </ul>
                    <h5>Matching</h5>
                    <ul>
                      <li>PDQ: Distance 14</li>
                      <li>Video MD5</li>
                    </ul>
                  </p>
                </div>
                <a href="#todo" className="btn btn-primary">
                  Edit
                </a>
              </div>
            </div>
          </div>
          <h2>External Signal Sources</h2>
          <div className="row mt-3">
            <div className="col-xl-4 col-lg-4 col-md-6 col-sm-6 col-xs-12 mb-4">
              <div className="card text-center">
                <div className="card-header text-white bg-success">
                  <h4 className="mb-0">Cat Dataset</h4>
                </div>
                <h6 className="card-subtitle mt-0 mb-0 text-muted">
                  ThreatExchange
                </h6>
                <div className="card-body text-left">
                  <p className="card-text">
                    <h5>Privacy Group</h5>
                    <ul>
                      <li>Cat Image Collaboration</li>
                    </ul>
                    <h5>Settings</h5>
                    <ul>
                      <li>✔️ SEEN status</li>
                      <li>✔️ True/False Positive</li>
                      <li>❌ Upload Signals</li>
                    </ul>
                  </p>
                </div>
                <a href="#todo" className="btn btn-primary">
                  Edit
                </a>
              </div>
            </div>
          </div>
        </Tab>
        <Tab eventKey="pipeline" title="Pipeline">
          Todo!
        </Tab>
      </Tabs>
    </>
  );
}
