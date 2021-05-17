/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState, useEffect} from 'react';
import {useHistory, useParams} from 'react-router-dom';
import {Col, Row, Table, Button} from 'react-bootstrap';

import {fetchHash, fetchImage} from '../Api';
import {CopyableHashField} from '../utils/TextFieldsUtils';
import {formatTimestamp} from '../utils/DateTimeUtils';
import {BlurUntilHoverImage} from '../utils/ImageUtils';
import ContentMatchTable from '../components/ContentMatchTable';
import FixedWidthCenterAlignedLayout from './layouts/FixedWidthCenterAlignedLayout';

export default function ContentDetails() {
  const history = useHistory();
  const {id} = useParams();
  const [actions, setActions] = useState([]);
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

  // TODO fetch actions once endpoint exists
  useEffect(() => {
    setActions([]);
  }, []);

  return (
    <FixedWidthCenterAlignedLayout title="Summary">
      <Row>
        <Col className="mb-4">
          <Button variant="link" href="#" onClick={() => history.goBack()}>
            &larr; Back to Matches
          </Button>
        </Col>
      </Row>
      <Row
        style={{
          minHeight: '450px',
        }}>
        <Col md={6}>
          <Table>
            <tbody>
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
                  {actions.length
                    ? 'TODO Render Actions Needs a Component'
                    : 'No actions performed'}
                </td>
              </tr>
            </tbody>
          </Table>
        </Col>
        <Col md={6}>
          <BlurUntilHoverImage src={img} />
        </Col>
      </Row>
      <ContentMatchTable contentKey={id} />
    </FixedWidthCenterAlignedLayout>
  );
}
