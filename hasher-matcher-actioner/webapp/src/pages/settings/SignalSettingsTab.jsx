/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';
import Card from 'react-bootstrap/Card';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import ListGroup from 'react-bootstrap/ListGroup';
import Button from 'react-bootstrap/Button';
import Badge from 'react-bootstrap/Badge';

export default function SignalSettingsTab() {
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
                <div>
                  <Badge pill variant="primary">
                    cat
                  </Badge>
                </div>
                <div>
                  <Badge pill variant="primary">
                    delete
                  </Badge>
                </div>
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
            <Button variant="primary" block>
              Edit
            </Button>
          </Card>
        </Col>
        <Col lg={4} sm={6} xs={12} className="mb-4">
          <div className="card text-center">
            <div className="card-header text-white bg-secondary">
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
            <Button variant="primary" block>
              Edit
            </Button>
          </div>
        </Col>
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
              <Badge pill variant="primary">
                cat
              </Badge>{' '}
              <Badge pill variant="primary">
                unverified
              </Badge>{' '}
              <Badge pill variant="info">
                low_precision
              </Badge>
              <h5>Matching</h5>
              <div>
                <Badge variant="success">PDQ</Badge> Distance 17
              </div>
            </Card.Text>
          </Card.Body>
          <ListGroup variant="flush" className="text-left">
            <ListGroup.Item>
              <h5>Shared From: Cat Dataset</h5>
              <h6>Label Map</h6>
              {'low_precision → '}
              <Badge pill variant="info">
                low_precision
              </Badge>
            </ListGroup.Item>
          </ListGroup>
          <Button variant="primary" block>
            Edit
          </Button>
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
            <Button variant="primary" block>
              Edit
            </Button>
          </Card>
        </Col>
      </Row>
    </>
  );
}
