/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React, {useEffect, useState} from 'react';
import {Col, Row, Button} from 'react-bootstrap';
import {fetchIndexesLastModified, rebuildAllIndexes} from '../../Api';
import {timeAgoForDate} from '../../utils/DateTimeUtils';
import SettingsTabPane from './SettingsTabPane';

export default function IndexSettingsTab(): JSX.Element {
  const [lastModified, setLastModified] = useState<Date>();
  const [rebuilding, setRebuilding] = useState<boolean>(false);
  const [pollBuster, setPollBuster] = useState<number>(0);

  useEffect(() => {
    fetchIndexesLastModified().then(setLastModified);
  }, [pollBuster]);

  const rebuild = () => {
    setRebuilding(true);
    rebuildAllIndexes().then(() => {
      setRebuilding(false);
      // Trigger refresh of page contents.
      setPollBuster(pollBuster + 1);
    });
  };

  return (
    <SettingsTabPane>
      <Row>
        <Col>
          <SettingsTabPane.Title>Indexes</SettingsTabPane.Title>
        </Col>
      </Row>
      <Row>
        <Col>
          Indexes are how your content is quickly matched against sources. They
          are frequently rebuilt automatically. However, if you want to
          force-update the index, you can do that here.
        </Col>
      </Row>

      <Row>
        <Col className="mt-4">
          <p>
            <b>Index Last Built: </b>
            {lastModified ? timeAgoForDate(lastModified) : <i>Loading...</i>}
          </p>
          <Button disabled={rebuilding} onClick={rebuild}>
            Rebuild Indexes
          </Button>
        </Col>
      </Row>
    </SettingsTabPane>
  );
}
