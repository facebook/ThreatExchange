/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useEffect, useState} from 'react';
import PropTypes from 'prop-types';
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

import {fetchStats} from '../Api';
import {StatNames, StatsTimeSpans} from '../utils/constants';
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
  const [timeSpan, setTimeSpan] = useState(StatsTimeSpans.HOURS_24);

  return (
    <Container className="m-4">
      <Row>
        <Col
          xs={6}
          className="mb-4 d-flex align-items-baseline justify-content-end">
          <div className="align-middle mr-2">Show statistics for the last</div>
          <DropdownButton
            as={ButtonGroup}
            id="dropdown-time-span-picker"
            variant="secondary"
            title={getDisplayTimeSpan(timeSpan)}>
            {Object.entries(StatsTimeSpans)
              .map(entry => entry[1]) // Get values only, no keys.
              .map((timeSpanChoice, index) => (
                <Dropdown.Item
                  key={`time-span-picker-${timeSpanChoice}`}
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
          <StatCard statName={StatNames.HASHES} timeSpan={timeSpan} />
          <StatCard statName={StatNames.MATCHES} timeSpan={timeSpan} />
        </Col>
      </Row>
    </Container>
  );
}

function StatCard({statName, timeSpan}) {
  const [card, setCard] = useState(undefined);

  useEffect(() => {
    fetchStats(statName, timeSpan).then(response => {
      setCard(response.card);
    });
  }, [timeSpan]);

  return card === undefined ? (
    <Spinner animation="border" role="status">
      <span className="sr-only">Loading...</span>
    </Spinner>
  ) : (
    <Card key={`stat-card-${statName}`} className="mb-4">
      <Card.Header>
        <GraphWithNumberWidget graphData={toUFlotFormat(card.graph_data)} />
        <h1>{getDisplayNumber(card.number)}</h1>
      </Card.Header>
      <Card.Body>
        <Card.Title>{getDisplayTitle(statName)}</Card.Title>
        <Card.Subtitle>
          Processed in the last {getDisplayTimeSpan(card.time_span)}.
        </Card.Subtitle>
      </Card.Body>
    </Card>
  );
}

StatCard.propTypes = {
  statName: PropTypes.string.isRequired,
  timeSpan: PropTypes.string.isRequired,
};
