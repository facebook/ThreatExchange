/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState, useEffect} from 'react';
import {useHistory, useParams} from 'react-router-dom';
import {Button, Col, Collapse, Row} from 'react-bootstrap';
import Spinner from 'react-bootstrap/Spinner';

import {fetchMatchDetails, fetchHash, fetchImage} from './Api';
import {CopyableHashField, CopyableTextField} from './utils/TextFieldsUtils';
import {formatTimestamp} from './utils/DateTimeUtils';
import {BlurUntilHoverImage} from './utils/ImageUtils';

export default function MatchDetails() {
  const history = useHistory();
  const {id} = useParams();
  const [showNewReactionButtons, setShowNewReactionButtons] = useState(false);
  const [reaction, setReaction] = useState('Seen');
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
      <h1>Match Details</h1>
      <Row>
        <Col md={6}>
          <table className="table">
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
              <td>Reaction (Mocked):</td>
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
                    <p className="mt-3">Change reaction to...</p>
                    <Button
                      size="sm"
                      variant="outline-primary"
                      onClick={() => {
                        setReaction('Positive');
                        setShowNewReactionButtons(false);
                      }}>
                      Positive
                    </Button>
                    <Button
                      className="ml-2"
                      size="sm"
                      variant="outline-primary">
                      False Positive
                    </Button>
                  </div>
                </Collapse>
              </td>
            </tr>
          </table>
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
  }, []);

  return (
    <>
      <Spinner hidden={matchDetails !== null} animation="border" role="status">
        <span className="sr-only">Loading...</span>
      </Spinner>
      <Collapse in={matchDetails !== null}>
        <Row>
          <Col md={12}>
            <table className="table mt-4">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Type</th>
                  <th>Indicator</th>
                  <th>Last Updated</th>
                  <th>Tags (Mocked)</th>
                  <th>Status (Mocked)</th>
                  <th>Partners with Opinions (Mocked)</th>
                  <th>Action Taken (Mocked)</th>
                </tr>
              </thead>
              <tbody>
                {matchDetails !== null && matchDetails.length ? (
                  matchDetails.map(match => (
                    <tr className="align-middle" key={match.signal_id}>
                      <td>
                        <CopyableTextField text={match.signal_id} />
                      </td>
                      <td>HASH_PDQ</td>
                      <CopyableHashField text={match.signal_hash} />
                      <td>{formatTimestamp(match.updated_at)}</td>
                      <td>tag1, tag2</td>
                      <td>UNKNOWN</td>
                      <td>app1, app2</td>
                      <td>Delete</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5}>No Matches Found.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </Col>
        </Row>
      </Collapse>
    </>
  );
}
