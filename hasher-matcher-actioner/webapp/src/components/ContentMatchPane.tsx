/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React, {useEffect, useState} from 'react';
import {Link} from 'react-router-dom';
import PropTypes from 'prop-types';
import {Container, Row, Col, ResponsiveEmbed} from 'react-bootstrap';
import {fetchPreviewURL, fetchContentDetails, ContentDetails} from '../Api';
import {BlurImage} from '../utils/MediaUtils';
import {formatTimestamp} from '../utils/DateTimeUtils';

type ContentMatchPaneProps = {
  contentId: string;
  signalId: string;
  signalSource: string;
};

/**
 * For a content key that matched a signal, show a summary and link to other
 * routes that show more information.
 */
export default function ContentMatchPane({
  contentId,
  signalId,
  signalSource,
}: ContentMatchPaneProps): JSX.Element {
  const [contentDetails, setContentDetails] = useState<ContentDetails>();
  const [img, setImage] = useState<string>('');

  useEffect(() => {
    fetchPreviewURL(contentId)
      .then(result => {
        setImage(result.preview_url);
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
    (!contentDetails && <p>Loading...</p>) || (
      <Container>
        <Row>
          <Col className="p-4 text-center">
            <ResponsiveEmbed aspectRatio="16by9">
              <BlurImage src={img} />
            </ResponsiveEmbed>
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
              <Link to={`?contentId=${contentId}`}>
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
