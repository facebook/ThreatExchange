/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React, {useState, useEffect} from 'react';
import {Col, Collapse, Row, Table, Button} from 'react-bootstrap';
import Spinner from 'react-bootstrap/Spinner';

import {fetchContentActionHistory, ContentActionHistoryRecord} from '../Api';
import {CopyableTextField} from '../utils/TextFieldsUtils';
import {formatTimestamp} from '../utils/DateTimeUtils';

const DEFAULT_NUM_ROWS = 2;

type ActionHistoryTableProps = {
  contentKey: string;
};

export default function ActionHistoryTable(
  {contentKey}: ActionHistoryTableProps = {
    contentKey: '',
  },
): JSX.Element {
  const [actionHistory, setActionHistory] =
    useState<ContentActionHistoryRecord[]>();
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    fetchContentActionHistory(contentKey).then(result => {
      if (result && result.action_history) {
        result.action_history.sort(
          (event1, event2) =>
            new Date(event2.performed_at).getTime() -
            new Date(event1.performed_at).getTime(),
        );
        setActionHistory(result.action_history);
      }
    });
  }, [contentKey]);

  return (
    <>
      <Spinner hidden={actionHistory !== null} animation="border" role="status">
        <span className="sr-only">Loading...</span>
      </Spinner>
      <Collapse in={actionHistory !== null}>
        <Row>
          <Col md={12}>
            <h3>Action History</h3>

            <Table responsive className="mt-2" title="Action History">
              {actionHistory && actionHistory.length ? (
                <>
                  <thead>
                    <tr>
                      <th>Action Label</th>
                      <th>Performed At</th>
                    </tr>
                  </thead>
                  <tbody>
                    {actionHistory.map((actionEvent, index) => {
                      if (index < DEFAULT_NUM_ROWS || showAll) {
                        return (
                          <tr key={actionEvent.performed_at}>
                            <td>
                              <CopyableTextField
                                text={actionEvent.action_label}
                              />
                            </td>
                            <td>{formatTimestamp(actionEvent.performed_at)}</td>
                          </tr>
                        );
                      }
                      return null;
                    })}
                    <tr>
                      <td colSpan={2}>
                        {`Total Action Events ${actionHistory.length}`}
                        {actionHistory.length > DEFAULT_NUM_ROWS ? (
                          <Button
                            variant="link"
                            className="float-right"
                            href="#"
                            onClick={() => setShowAll(!showAll)}>
                            {showAll ? 'hide' : '...see all'}
                          </Button>
                        ) : null}
                      </td>
                    </tr>
                  </tbody>
                </>
              ) : (
                <tbody>
                  <tr>
                    <td colSpan={2}>No action history found for content.</td>
                  </tr>
                </tbody>
              )}
            </Table>
          </Col>
        </Row>
      </Collapse>
    </>
  );
}
