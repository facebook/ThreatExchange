/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React, {useEffect, useState} from 'react';
import PropTypes from 'prop-types';
import {
  Alert,
  Row,
  Col,
  Card,
  ButtonGroup,
  Dropdown,
  DropdownButton,
  Spinner,
} from 'react-bootstrap';
import {fetchStats, StatsCard} from '../Api';
import {StatNames, StatsTimeSpans} from '../utils/constants';
import GraphWithNumberWidget from '../components/GraphWithNumberWidget';
import shortenNumRepr from '../utils/NumberUtils';
import FixedWidthCenterAlignedLayout from './layouts/FixedWidthCenterAlignedLayout';

function getDisplayTitle(statName: string) {
  return (
    {
      hashes: 'Photos Processed',
      matches: 'Photos Matched',
      actions: 'Actions Taken',
    }[statName] || 'Unknown Statistic'
  );
}

function getDisplayTimeSpan(timeSpan: string) {
  return (
    {
      '24h': '24 hours',
      '1h': '1 hour',
      '7d': '7 days',
    }[timeSpan] || 'unknown period'
  );
}

/**
 * Squeeze large numbers into more digestible values.
 * eg. 1,079,234 -> 1M+, 1,508 -> 1.5K
 *
 * @param {int} number
 * @returns string
 */
function getDisplayNumber(number: number) {
  return shortenNumRepr(number);
}

/**
 * Returns a list of two lists. First one is timestamps, second one is values.
 */
function toUFlotFormat(
  graphData: Array<[number, number]>,
): [number[], number[]] {
  const timestamps = [] as number[];
  const values = [] as number[];

  graphData.forEach(entry => {
    timestamps.push(entry[0]);
    values.push(entry[1]);
  });

  values[0] = 0;
  values[values.length - 1] = 0;

  return [timestamps, values];
}

function StatCardLoading({statName}: {statName: string}): JSX.Element {
  return (
    <Card key={`stat-card-${statName}`} className="mb-4">
      <Card.Body>
        <Col>
          <h4 className="text-muted font-weight-light">
            <Spinner
              as="span"
              animation="border"
              role="status"
              aria-hidden="true"
            />
            <span>&nbsp;Loading stats for {statName}...</span>
          </h4>
        </Col>
      </Card.Body>
    </Card>
  );
}

function StatCardError({statName}: {statName: string}): JSX.Element {
  return (
    <Card key={`stat-card-${statName}`} className="mb-4">
      <Card.Body>
        <Col>
          {process.env.REACT_APP_AWS_DASHBOARD_URL ? (
            <Alert variant="secondary">
              Additional metrics for the system&apos;s underlying implementation
              can be found{' '}
              <a
                href={process.env.REACT_APP_AWS_DASHBOARD_URL}
                target="_blank"
                rel="noreferrer">
                here.
              </a>{' '}
              (AWS Console authentication required)
            </Alert>
          ) : (
            <Alert variant="secondary">
              Detailed metrics need to be enabled during deployment.
            </Alert>
          )}
        </Col>
      </Card.Body>
    </Card>
  );
}

function StatCard({
  statName,
  timeSpan,
}: {
  statName: string;
  timeSpan: string;
}): JSX.Element {
  // Card can be undefined, the card object, or 'failed' string.
  // Failed string will have a different repr.
  const [card, setCard] = useState<string | StatsCard>('');

  useEffect(() => {
    fetchStats(statName, timeSpan)
      .then(response => {
        setCard(response.card);
      })
      .catch(() => {
        setCard('failed');
      });
  }, [timeSpan]);

  if (card === '') {
    return <StatCardLoading statName={statName} />;
  }
  if (card === 'failed') {
    return <StatCardError statName={statName} />;
  }

  return (
    <Card key={`stat-card-${statName}`} className="mb-4">
      <Card.Body>
        <Row>
          <Col xs={8}>
            <h2 style={{fontWeight: 300}}>{getDisplayTitle(statName)}</h2>
          </Col>
          <Col xs={4} className="text-right">
            <h1>{getDisplayNumber((card as StatsCard).time_span_count)}</h1>
            <small className="text-muted">
              in the last {getDisplayTimeSpan((card as StatsCard).time_span)}.
            </small>
          </Col>
        </Row>
      </Card.Body>
      <Card.Footer>
        <GraphWithNumberWidget
          graphData={toUFlotFormat((card as StatsCard).graph_data)}
        />
      </Card.Footer>
    </Card>
  );
}

/**
 * Will be renamed as Dashboard.jsx once we replace it.
 */
export default function Dashboard(): JSX.Element {
  const [timeSpan, setTimeSpan] = useState(StatsTimeSpans.HOURS_24);

  return (
    <FixedWidthCenterAlignedLayout title="HMA Dashboard">
      <Row>
        <Col className="mb-4 d-flex align-items-baseline justify-content-end">
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
        <Col>
          <StatCard statName={StatNames.HASHES} timeSpan={timeSpan} />
          <StatCard statName={StatNames.MATCHES} timeSpan={timeSpan} />
        </Col>
      </Row>
      <Row>
        <Col>
          <Alert variant="secondary">
            Additional metrics for the system&apos;s underlying implementation
            can be found{' '}
            <a
              href={process.env.REACT_APP_AWS_DASHBOARD_URL}
              target="_blank"
              rel="noreferrer">
              here.
            </a>{' '}
            (AWS Console authentication required)
          </Alert>
        </Col>
      </Row>
    </FixedWidthCenterAlignedLayout>
  );
}

StatCard.propTypes = {
  statName: PropTypes.string.isRequired,
  timeSpan: PropTypes.string.isRequired,
};

StatCardLoading.propTypes = {
  statName: PropTypes.string.isRequired,
};

StatCardError.propTypes = {
  statName: PropTypes.string.isRequired,
};
