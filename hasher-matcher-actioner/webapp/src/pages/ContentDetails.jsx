/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState, useEffect} from 'react';
import {useHistory, useParams} from 'react-router-dom';
import {Col, Row, Table, Button} from 'react-bootstrap';

import {fetchHash, fetchImage, fetchContentDetails} from '../Api';
import {CopyableHashField} from '../utils/TextFieldsUtils';
import {formatTimestamp} from '../utils/DateTimeUtils';
import {BlurImage} from '../utils/ImageUtils';
import ContentMatchTable from '../components/ContentMatchTable';
import ActionHistoryTable from '../components/ActionHistoryTable';
import FixedWidthCenterAlignedLayout from './layouts/FixedWidthCenterAlignedLayout';

export default function ContentDetails() {
  const history = useHistory();
  const {id} = useParams();
  const [contentDetails, setContentDetails] = useState(null);
  const [hashDetails, setHashDetails] = useState(null);
  const [img, setImage] = useState(null);

  // Catch the following promises because it is possible for the endpoint to
  // return error codes if the content values are not yet populated if users come
  /// to this page right after submit
  useEffect(() => {
    fetchHash(id)
      .then(hash => {
        setHashDetails(hash);
      })
      .catch(_ => {
        setHashDetails(null);
      });
  }, []);

  useEffect(() => {
    fetchImage(id)
      .then(result => {
        setImage(URL.createObjectURL(result));
      })
      .catch(_ => {
        // ToDo put a 'not found' image
        setImage(null);
      });
  }, []);

  useEffect(() => {
    fetchContentDetails(id)
      .then(result => {
        setContentDetails(result);
      })
      .catch(_ => {
        setContentDetails(null);
      });
  }, []);

  return (
    <FixedWidthCenterAlignedLayout title="Summary">
      <Row>
        <Col className="mb-4">
          <Button variant="link" href="#" onClick={() => history.goBack()}>
            &larr; Back
          </Button>
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
          <BlurImage src={img} />
        </Col>
      </Row>
      <ContentMatchTable contentKey={id} />
    </FixedWidthCenterAlignedLayout>
  );
}
