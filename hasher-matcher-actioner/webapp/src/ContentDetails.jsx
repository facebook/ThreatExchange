/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState, useEffect} from 'react';
import {useHistory, useParams} from 'react-router-dom';
import {Button, Col, Collapse, Row, Table} from 'react-bootstrap';
import Spinner from 'react-bootstrap/Spinner';

import {
  fetchMatchDetails,
  fetchHash,
  fetchImage,
  updateContentStatus,
} from './Api';
import {CopyableHashField, CopyableTextField} from './utils/TextFieldsUtils';
import {formatTimestamp} from './utils/DateTimeUtils';
import {BlurUntilHoverImage} from './utils/ImageUtils';

export default function MatchDetails() {
  const history = useHistory();
  const {id} = useParams();
  const [showNewReactionButtons, setShowNewReactionButtons] = useState(false);
  const [reaction, setReaction] = useState('Mocked');
  const [hashDetails, setHashDetails] = useState(null);
  const [img, setImage] = useState(null);

  useEffect(() => {
    fetchHash(id).then(hash => {
      setHashDetails(hash);
    });
  }, []);

  useEffect(() => {
    fetchImage(id).then(result => {
      setImage(URL.createObjectURL(result));
    });
  }, []);

  return (
    <>
      <button
        type="submit"
        className="float-right btn btn-primary"
        onClick={() => history.goBack()}>
        Back
      </button>
      <h1>Summary</h1>
      <Row>
        <Col md={6}>
          <Table>
            <tr>
              <td>Content ID:</td>
              <td>{id}</td>
            </tr>
            <tr>
              <td>Content Hash:</td>
              <CopyableHashField
                text={
                  hashDetails
                    ? hashDetails.content_hash ?? 'Not found'
                    : 'loading...'
                }
              />
            </tr>
            <tr>
              <td>Hashed on:</td>
              <td>
                {hashDetails
                  ? formatTimestamp(hashDetails.updated_at)
                  : 'loading...'}
              </td>
            </tr>
            <tr>
              <td>Status:</td>
              <td>
                {reaction}
                <Button
                  className="float-right"
                  size="sm"
                  variant="outline-primary"
                  onClick={() =>
                    setShowNewReactionButtons(!showNewReactionButtons)
                  }>
                  {showNewReactionButtons ? 'Cancel' : 'Change'}
                </Button>
                <Collapse in={showNewReactionButtons}>
                  <div>
                    <p className="mt-3">Update to...</p>
                    <Button
                      size="sm"
                      variant="outline-primary"
                      onClick={() => {
                        const newStatus = 'Status 1 (Mocked)';
                        updateContentStatus(id, newStatus).then(() => {
                          setShowNewReactionButtons(false);
                          setReaction(newStatus);
                        });
                      }}>
                      Action 1
                    </Button>
                    <Button
                      className="ml-2"
                      size="sm"
                      variant="outline-primary"
                      onClick={() => {
                        const newStatus = 'Status 2 (Mocked)';
                        updateContentStatus(id, newStatus).then(() => {
                          setShowNewReactionButtons(false);
                          setReaction(newStatus);
                        });
                      }}>
                      Action 2
                    </Button>
                    <Button
                      className="ml-2"
                      size="sm"
                      variant="outline-primary"
                      onClick={() => {
                        const newStatus = 'To Delete (Mocked)';
                        updateContentStatus(id, newStatus).then(() => {
                          setShowNewReactionButtons(false);
                          setReaction(newStatus);
                        });
                      }}>
                      Delete
                    </Button>
                  </div>
                </Collapse>
              </td>
            </tr>
          </Table>
        </Col>
        <Col md={6}>
          <BlurUntilHoverImage src={img} />
        </Col>
      </Row>
      <MatchesList contentKey={id} />
    </>
  );
}

function MatchesList(props) {
  const [matchDetails, setMatchDetails] = useState(null);
  // eslint-disable-next-line react/prop-types
  const {contentKey} = props;
  useEffect(() => {
    fetchMatchDetails(contentKey).then(matches => {
      setMatchDetails(matches.match_details);
    });
  }, [contentKey]);

  return (
    <>
      <Spinner hidden={matchDetails !== null} animation="border" role="status">
        <span className="sr-only">Loading...</span>
      </Spinner>
      <Collapse in={matchDetails !== null}>
        <Row>
          <Col md={12}>
            <h3>Matches</h3>
            <Table responsive className="mt-4" title="Matches">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Type</th>
                  <th>Indicator</th>
                  <th>Last Updated</th>
                  <th>Dataset</th>
                  <th>Opinion</th>
                  <th>Tags</th>
                </tr>
              </thead>
              <tbody>
                {matchDetails !== null && matchDetails.length ? (
                  matchDetails.map((match, index) => (
                    <>
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
                          <td>{metadata.dataset}</td>
                          <td>{metadata.opinion}</td>
                          <td>{metadata.tags.join(', ')}</td>
                        </tr>
                      ))}
                    </>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5}>No Matches Found.</td>
                  </tr>
                )}
              </tbody>
            </Table>
          </Col>
        </Row>
      </Collapse>
    </>
  );
}
