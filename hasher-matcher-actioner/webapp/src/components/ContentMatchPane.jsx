/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useEffect, useState} from 'react';
import {Link} from 'react-router-dom';
import PropTypes from 'prop-types';
import {Container, Row, Col} from 'react-bootstrap';
import {fetchHash, fetchImage, fetchContentDetails} from '../Api';
import {BlurImage} from '../utils/MediaUtils';
import {formatTimestamp} from '../utils/DateTimeUtils';

/**
 * For a content key that matched a signal, show a summary and link to other
 * routes that show more information.
 */
export default function ContentMatchPane({contentId, signalId, signalSource}) {
  const [hashDetails, setHashDetails] = useState(null);
  const [contentDetails, setContentDetails] = useState(null);
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

  useEffect(() => {
    fetchContentDetails(contentId).then(result => {
      // Ensure placeholders don't get displayed. TODO: Move this to the API.
      const additionalFields = result.additional_fields.filter(
        x => x !== 'Placeholder',
      );

      setContentDetails({...result, additional_fields: additionalFields});
    });
  }, [contentId]);

  return (
    (hashDetails === null && <p>Loading...</p>) || (
      <Container>
        <Row>
          {/* Avoid explicit padding if possible when re-doing this page. */}
          <Col className="p-4 text-center" style={{minHeight: '200px'}}>
            <BlurImage src={img} />
          </Col>
        </Row>
        <Row>
          <Col className="p-4">
            <h4 className="mt-4">Content Details</h4>
            <p>
              Last Submitted to HMA:{' '}
              <b>
                {contentDetails && contentDetails.updated_at
                  ? formatTimestamp(contentDetails.updated_at)
                  : 'Unknown'}
              </b>
            </p>

            <h4 className="mt-4">Additional Fields</h4>
            {contentDetails && contentDetails.additional_fields.length !== 0 ? (
              contentDetails.additional_fields.map(field => <li>{field}</li>)
            ) : (
              <p>No additional fields provided</p>
            )}

            <p className="mt-4">
              <Link to={`/matches/${contentId}`}>
                Open the details page for content
              </Link>
            </p>

            <h4 className="mt-4">Filter results on this page</h4>
            <li>
              <Link to={`?signalId=${signalSource}|${signalId}`}>
                Show matches for this signal
              </Link>
            </li>

            <li>
              <Link to={`?contentId=images/${contentId}`}>
                Show all matches for this content
              </Link>
            </li>
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
