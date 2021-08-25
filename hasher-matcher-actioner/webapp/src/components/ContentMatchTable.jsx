/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState, useEffect} from 'react';
import {Col, Collapse, Row, Table, Toast} from 'react-bootstrap';
import PropTypes from 'prop-types';
import Spinner from 'react-bootstrap/Spinner';

import {fetchMatchDetails} from '../Api';
import {CopyableHashField, CopyableTextField} from '../utils/TextFieldsUtils';
import {formatTimestamp} from '../utils/DateTimeUtils';

import OpinionTableCell from './OpinionTableCell';

export default function ContentMatchTable({contentKey}) {
  const [matchDetails, setMatchDetails] = useState(null);
  useEffect(() => {
    fetchMatchDetails(contentKey).then(matches => {
      setMatchDetails(matches.match_details);
    });
  }, [contentKey]);

  const [showToast, setShowToast] = useState(false);
  return (
    <>
      <Spinner hidden={matchDetails !== null} animation="border" role="status">
        <span className="sr-only">Loading...</span>
      </Spinner>
      <div className="feedback-toast-container">
        <Toast
          onClose={() => setShowToast(false)}
          show={showToast}
          delay={5000}
          autohide>
          <Toast.Header>
            <strong className="mr-auto">Submitted</strong>
            <small>Thanks!</small>
          </Toast.Header>
          <Toast.Body>
            Please wait for the requested change to propagate
          </Toast.Body>
        </Toast>
      </div>
      <Collapse in={matchDetails !== null}>
        <Row>
          <Col md={12}>
            <h3>Matches</h3>
            <Table responsive className="mt-2" title="Matches">
              <thead>
                <tr>
                  <th>MatchedSignal ID</th>
                  <th>MatchedSignal Type</th>
                  <th>MatchedSignal</th>
                  <th>Last Updated</th>
                  <th>Privacy Group</th>
                  <th>Opinion</th>
                  <th>Classifications</th>
                </tr>
              </thead>
              {matchDetails !== null && matchDetails.length ? (
                matchDetails.map((match, index) => (
                  <tbody key={match.signal_id}>
                    {match.metadata.map((metadata, subIndex) => (
                      <tr
                        style={index % 2 ? {} : {background: '#dddddd'}}
                        className="align-middle"
                        key={match.signal_id + metadata.dataset}>
                        {subIndex === 0 ? (
                          <>
                            <td>
                              <CopyableTextField text={match.signal_id} />
                            </td>
                            <td>{match.signal_type}</td>
                            <CopyableHashField text={match.signal_hash} />
                            <td>{formatTimestamp(match.updated_at)}</td>
                          </>
                        ) : (
                          <>
                            <td />
                            <td />
                            <td />
                            <td />
                          </>
                        )}
                        <td>{metadata.privacy_group_id}</td>
                        <td>
                          <OpinionTableCell
                            privacyGroupId={metadata.privacy_group_id}
                            signalId={match.signal_id}
                            signalSource={match.signal_source}
                            opinion={metadata.opinion}
                            pendingOpinionChange={
                              metadata.pending_opinion_change
                            }
                            setShowToast={setShowToast}
                          />
                        </td>
                        <td>{metadata.tags.join(', ')}</td>
                      </tr>
                    ))}
                  </tbody>
                ))
              ) : (
                <tbody>
                  <tr>
                    <td colSpan={5}>No Matches found for this Content.</td>
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

ContentMatchTable.propTypes = {
  contentKey: PropTypes.string,
};

ContentMatchTable.defaultProps = {
  contentKey: undefined,
};
