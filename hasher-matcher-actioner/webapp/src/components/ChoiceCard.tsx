/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React from 'react';
import {Col, Row, Card, Form} from 'react-bootstrap';

type ChoiceCardProps = {
  label: string;
  description: string;
  selected: boolean;
  onSelect: () => void;
};

export default function ChoiceCard({
  label,
  description,
  onSelect,
  selected,
}: ChoiceCardProps): JSX.Element {
  return (
    <Card
      border={selected ? 'primary' : ''}
      //   text={selected ? 'white' : 'dark'}
      style={{cursor: 'pointer'}}
      onClick={() => onSelect()}>
      <Card.Body>
        <Row>
          <Col xs="1">
            <Form.Check type="radio" checked={selected} />
          </Col>
          <Col xs="11">
            <Card.Title>{label}</Card.Title>
            <Card.Text>{description}</Card.Text>
          </Col>
        </Row>
      </Card.Body>
    </Card>
  );
}
