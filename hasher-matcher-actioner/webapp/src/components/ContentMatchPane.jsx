/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useEffect, useState} from 'react';
import {Link} from 'react-router-dom';
import PropTypes from 'prop-types';
import {Container, Row, Col} from 'react-bootstrap';
import {fetchHash, fetchImage} from '../Api';
import {BlurUntilHoverImage} from '../utils/ImageUtils';

/**
 * For a content key that matched a signal, show a summary and link to other
 * routes that show more information.
 */
export default function ContentMatchPane({contentId, signalId, signalSource}) {
  const [hashDetails, setHashDetails] = useState(null);
  const [img, setImage] = useState(null);

  useEffect(() => {
    fetchHash(contentId).then(hash => {
      setHashDetails(hash);
    });
  }, [contentId]);

  useEffect(() => {
    fetchImage(contentId)
      .then(result => {
        setImage(URL.createObjectURL(result));
      })
      .catch(() => {
        setImage(
          // TODO: Use a better in-house error message. Perhaps not blur it?
          'https://image.shutterstock.com/image-vector/mission-failed-text-on-red-260nw-1633188751.jpg',
        );
      });
  }, [contentId]);

  return (
    (hashDetails === null && <p>Loading...</p>) || (
      <Container>
        <Row>
          {/* Avoid explicit padding if possible when re-doing this page. */}
          <Col className="p-4">
            <BlurUntilHoverImage src={img} />
          </Col>
        </Row>
        <Row>
          <Col md={3} className="p-4">
            Details
          </Col>
          <Col className="p-4">
            <Link to={`/matches/${contentId}`}>
              View Details for this match.
            </Link>
          </Col>
        </Row>
        <Row>
          <Col md={3} className="p-4">
            Signal
          </Col>
          <Col className="p-4">
            <Link to={`?signalId=${signalSource}|${signalId}`}>
              View Matches for Signal
            </Link>
          </Col>
        </Row>
        <Row>
          <Col md={3} className="p-4">
            Content
          </Col>
          <Col className="p-4">
            <Link to={`?contentId=images/${contentId}`}>
              View Matches of this Content
            </Link>
          </Col>
        </Row>
      </Container>
    )
  );
}

ContentMatchPane.propTypes = {
  contentId: PropTypes.string,
  signalId: PropTypes.string,
  signalSource: PropTypes.string,
};

ContentMatchPane.defaultProps = {
  contentId: undefined,
  signalId: undefined,
  signalSource: undefined,
};
