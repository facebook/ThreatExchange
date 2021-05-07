/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useEffect, useState} from 'react';
import {
  Container,
  Row,
  Col,
  Card,
  Spinner,
  ButtonGroup,
  Dropdown,
  DropdownButton,
} from 'react-bootstrap';

import {fetchStats, StatsTimeSpans} from '../Api';
import GraphWithNumberWidget from '../components/GraphWithNumberWidget';

function getDisplayTitle(statName) {
  return (
    {
      hashes: 'Photos Processed',
      matches: 'Photos Matched',
      actions: 'Actions Taken',
    }[statName] || 'Unknown Statistic'
  );
}

function getDisplayTimeSpan(timeSpan) {
  return (
    {
      '24h': '24 hours',
      '1h': '1 hour',
      '7d': '7 days',
    }[timeSpan] || 'unknown period'
  );
}

/**
 * Eventually, this should squeeze large numbers into more digestible values.
 * eg. 1,079,234 -> 1M+, 1,508 -> 1.5K
 *
 * @param {int} number
 * @returns string
 */
function getDisplayNumber(number) {
  return number;
}

/**
 * Returns a list of two lists. First one is timestamps, second one is values.
 */
function toUFlotFormat(graphData) {
  const timestamps = [];
  const values = [];

  graphData.forEach(entry => {
    timestamps.push(entry[0]);
    values.push(entry[1]);
  });

  values[0] = null;
  values[values.length - 1] = null;

  return [timestamps, values];
}

/**
 * Will be renamed as Dashboard.jsx once we replace it.
 */
export default function Dash() {
  const [statCards, setStatCards] = useState([]);
  const [timeSpan, setTimeSpan] = useState(StatsTimeSpans.HOURS_24);

  useEffect(() => {
    fetchStats(timeSpan).then(response => {
      setStatCards(response.cards);
    });
  }, [timeSpan]);

  return (
    <Container className="m-4">
      <Row>
        <Col xs={6} className="mb-4 d-flex justify-content-end">
          <div>Show statistics for the last</div>
          <DropdownButton
            as={ButtonGroup}
            id="dropdown-time-span-picker"
            variant="secondary"
            title={getDisplayTimeSpan(timeSpan)}>
            {Object.entries(StatsTimeSpans)
              .map(entry => entry[1]) // Get values only, no keys.
              .map((timeSpanChoice, index) => (
                <Dropdown.Item
                  eventKey={index}
                  onSelect={() => setTimeSpan(timeSpanChoice)}>
                  {getDisplayTimeSpan(timeSpanChoice)}
                </Dropdown.Item>
              ))}
          </DropdownButton>
        </Col>
      </Row>
      <Row>
        <Col xs={6}>
          {statCards.length === 0 ? (
            <Spinner animation="border" role="status">
              <span className="sr-only">Loading...</span>
            </Spinner>
          ) : (
            statCards.map(card => (
              <Card key={`stat-card-${card.stat_name}`} className="mb-4">
                <Card.Header>
                  <GraphWithNumberWidget
                    graphData={toUFlotFormat(card.graph_data)}
                  />
                  <h1>{getDisplayNumber(card.number)}</h1>
                </Card.Header>
                <Card.Body>
                  <Card.Title>{getDisplayTitle(card.stat_name)}</Card.Title>
                  <Card.Subtitle>
                    Processed in the last {getDisplayTimeSpan(card.time_span)}.
                  </Card.Subtitle>
                </Card.Body>
              </Card>
            ))
          )}
        </Col>
      </Row>
    </Container>
  );
}
