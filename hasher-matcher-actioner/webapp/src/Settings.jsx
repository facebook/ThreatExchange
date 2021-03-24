/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';
import Card from 'react-bootstrap/Card';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import Tabs from 'react-bootstrap/Tabs';
import Tab from 'react-bootstrap/Tab';
import ListGroup from 'react-bootstrap/ListGroup';

export default function Settings() {
  return (
    <>
      <Tabs defaultActiveKey="signals" id="setting-tabs">
        <Tab eventKey="signals" title="Signals">
          <SignalSettingsTab />
        </Tab>
        <Tab eventKey="pipeline" title="Pipeline">
          Todo!
        </Tab>
      </Tabs>
    </>
  );
}

function SignalSettingsTab() {
  return (
    <>
      <DataSets />
      <ExternalSignalSources />
    </>
  );
}

function DataSets() {
  return (
    <>
      <h2 className="mt-4">Datasets</h2>
      <Row className="mt-3">
        <DataSet />
        <Col lg={4} sm={6} xs={12} className="mb-4">
          <Card className="text-center">
            <Card.Header className="text-white bg-success">
              <h4 className="mb-0">Verified Cat Imagery</h4>
            </Card.Header>
            <Card.Subtitle className="mt-0 mb-0 text-muted">
              Shared
            </Card.Subtitle>
            <Card.Body className="text-left">
              <Card.Text>
                <h5>Labels</h5>
                <ul>
                  <li>cat</li>
                  <li>delete</li>
                </ul>
                <h5>Matching</h5>
                <ul>
                  <li>PDQ: Distance 31</li>
                </ul>
              </Card.Text>
            </Card.Body>
            <ListGroup variant="flush" className="text-left">
              <ListGroup.Item>
                <h5>Share To: Cat Dataset</h5>
                <h6>Labels</h6>
                <ul>
                  <li>cat</li>
                </ul>
              </ListGroup.Item>
            </ListGroup>
            <a href="#todo" className="btn btn-primary">
              Edit
            </a>
          </Card>
        </Col>
        <div className="col-xl-4 col-lg-4 col-md-6 col-sm-6 col-xs-12 mb-4">
          <div className="card text-center">
            <div className="card-header text-white bg-success">
              <h4 className="mb-0">Dog Media</h4>
            </div>
            <div className="card-body text-left">
              <p className="card-text">
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
      </Row>
    </>
  );
}

function DataSet() {
  return (
    <>
      <Col lg={4} sm={6} xs={12} className="mb-4">
        <Card className="text-center">
          <Card.Header className="text-white bg-success">
            <h4 className="mb-0">Collboration on Cat Imagery</h4>
          </Card.Header>
          <Card.Subtitle className="mt-0 mb-0 text-muted">Shared</Card.Subtitle>
          <Card.Body className="text-left">
            <Card.Text>
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
            </Card.Text>
          </Card.Body>
          <ListGroup variant="flush" className="text-left">
            <ListGroup.Item>
              <h5>Shared From: Cat Dataset</h5>
              <h6>Label Map</h6>
              <ul>
                <li>low_precision → *</li>
              </ul>
            </ListGroup.Item>
          </ListGroup>
          <a href="#todo" className="btn btn-primary">
            Edit
          </a>
        </Card>
      </Col>
    </>
  );
}

function ExternalSignalSources() {
  return (
    <>
      <h2>External Signal Sources</h2>
      <SignalSource />
    </>
  );
}

function SignalSource() {
  return (
    <>
      <Row className="mt-3">
        <Col lg={4} sm={6} xs={12} className="mb-4">
          <Card className="text-center">
            <Card.Header className="text-white bg-success">
              <h4 className="mb-0">Cat Dataset</h4>
            </Card.Header>
            <Card.Subtitle className="mt-0 mb-0 text-muted">
              ThreatExchange
            </Card.Subtitle>
            <Card.Body className="text-left">
              <Card.Text>
                <div>
                  <h5 className="mb-0">Privacy Group</h5>
                  <div>Cat Image Collaboration</div>
                </div>
                <div className="mt-4">
                  <h5 className="mb-0">Settings</h5>
                  <div>✔️ Seen status</div>
                  <div>✔️ True/False Positive</div>
                  <div>❌ Upload Signals</div>
                </div>
              </Card.Text>
            </Card.Body>
            <a href="#todo" className="btn btn-primary">
              Edit
            </a>
          </Card>
        </Col>
      </Row>
    </>
  );
}
