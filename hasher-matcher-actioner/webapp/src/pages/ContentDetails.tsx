/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React, {useState, useEffect} from 'react';
import {useParams} from 'react-router-dom';
import {Col, Container, Row, Table} from 'react-bootstrap';

import {
  HashDetails,
  fetchHashDetails,
  fetchPreviewURL,
  ContentDetails,
  fetchContentDetails,
} from '../Api';
import {CopyableHashField} from '../utils/TextFieldsUtils';
import {formatTimestamp} from '../utils/DateTimeUtils';
import {getContentTypeForString} from '../utils/constants';
import ContentMatchTable from '../components/ContentMatchTable';
import ActionHistoryTable from '../components/ActionHistoryTable';
import FullWidthLeftAlignedLayout from './layouts/FullWidthLeftAlignedLayout';
import ContentPreview from '../components/ContentPreview';
import ReturnTo from '../components/ReturnTo';

type PageParam = {
  id: string;
};

export default function ContentDetailsSummary(): JSX.Element {
  const {id} = useParams<PageParam>();
  const [contentDetails, setContentDetails] = useState<ContentDetails>();
  const [hashDetails, setHashDetails] = useState<HashDetails>();
  const [img, setImage] = useState('');

  // Catch the following promises because it is possible for the endpoint to
  // return error codes if the content values are not yet populated if users come
  /// to this page right after submit
  useEffect(() => {
    fetchHashDetails(id)
      .then(hash => {
        setHashDetails(hash);
      })
      .catch(() => {
        setHashDetails(undefined);
      });
  }, []);

  useEffect(() => {
    fetchPreviewURL(id)
      .then(result => {
        setImage(result.preview_url);
      })
      .catch(() => {
        // ToDo put a 'not found' image
        setImage('');
      });
  }, []);

  useEffect(() => {
    fetchContentDetails(id)
      .then(result => {
        setContentDetails(result);
      })
      .catch(() => {
        setContentDetails(undefined);
      });
  }, []);

  return (
    <FullWidthLeftAlignedLayout title="Summary">
      <Container className="h-100 v-100" fluid>
        {/* ^ This container is everything below the header */}
        <Row>
          <Col className="mb-4">
            <ReturnTo />
          </Col>
        </Row>
        <Row
          style={{
            minHeight: '450px',
          }}>
          <Col md={6}>
            <h3>Content Details</h3>
            <Table>
              <tbody>
                <tr>
                  <td>Content ID:</td>
                  <td>{id}</td>
                </tr>
                <tr>
                  <td>Last Submitted:</td>
                  <td>
                    {contentDetails && contentDetails.updated_at
                      ? formatTimestamp(contentDetails.updated_at)
                      : 'Unknown'}
                  </td>
                </tr>
                <tr>
                  <td>Additional Fields:</td>
                  <td>
                    {contentDetails && contentDetails.additional_fields
                      ? contentDetails.additional_fields.join(', ')
                      : 'No additional fields provided'}
                  </td>
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
                  <td>Last Hashed on:</td>
                  <td>
                    {hashDetails
                      ? formatTimestamp(hashDetails.updated_at)
                      : 'loading...'}
                  </td>
                </tr>
              </tbody>
            </Table>
            <ActionHistoryTable contentKey={id} />
          </Col>
          <Col className="pt-4" md={6}>
            {img && contentDetails && contentDetails.content_type ? (
              <ContentPreview
                contentId={id}
                contentType={getContentTypeForString(
                  contentDetails.content_type,
                )}
                url={img}
              />
            ) : null}
          </Col>
        </Row>
        <ContentMatchTable contentKey={id} />
      </Container>
    </FullWidthLeftAlignedLayout>
  );
}
