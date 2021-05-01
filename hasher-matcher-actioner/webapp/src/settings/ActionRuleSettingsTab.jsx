/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

/* eslint-disable react/prop-types */

import React from 'react';
import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';

export default function ActionRuleSettingsTab() {
  return (
    <>
      <Container>
        <Row className="mt-3">
          <Col>
            <h1>Action Rules</h1>
            <p>
              Each rule indicates an action to be taken based on labels (e.g.,
              classification labels of a matching signal)
            </p>
          </Col>
        </Row>
      </Container>
    </>
  );
}
