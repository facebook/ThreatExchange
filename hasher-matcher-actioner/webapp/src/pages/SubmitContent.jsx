/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState} from 'react';
import {
  Col,
  Button,
  Row,
  Form,
  Collapse,
  Spinner,
  Alert,
} from 'react-bootstrap';
import {Link} from 'react-router-dom';

import {submitContent, submitContentUpload} from '../Api';
import {SUBMISSION_TYPE} from '../utils/constants';

import {
  ContentIdAndTypeField,
  PhotoUploadField,
  OptionalMetadataField,
  NotYetSupportedField,
} from '../components/SubmitContentFields';
import FixedWidthCenterAlignedLayout from './layouts/FixedWidthCenterAlignedLayout';

const FORM_DEFAULTS = {
  submissionType: undefined,
  contentId: undefined,
  contentType: 'PHOTO',
  contentRef: undefined,
};

export default function SubmitContent() {
  const [submitting, setSubmitting] = useState(false);
  const [submittedId, setSubmittedId] = useState(undefined);
  const [submissionType, setSubmissionType] = useState('');
  const [submissionMetadata, setSubmissionMetadata] = useState({});
  const [inputs, setInputs] = useState(FORM_DEFAULTS);

  // for most input changes we only need to take the input name and store the event value
  const handleInputChange = event => {
    event.persist();
    setInputs(inputs_ => ({
      ...inputs_,
      [event.target.name]: event.target.value,
    }));
  };

  // image upload is a special case so that we can do the following:
  // - give a preview of the image to user
  // - auto populate the content id if it is currently empty
  const handleInputChangeUpload = event => {
    const file = event.nativeEvent.path[0].files[0];
    const contentId = inputs.contentId ?? file.name;
    setInputs(inputs_ => ({
      ...inputs_,
      contentId,
      [event.target.name]: {
        preview: URL.createObjectURL(file),
        raw: file,
      },
    }));
  };

  const packageMetadata = () => {
    const entries = [];
    Object.values(submissionMetadata).forEach(entry =>
      // store key:value for now to avoid collisions/overwrite of repeats
      // exact extra additional fields spec should be established in documentation
      entries.push(`${entry.key}:${entry.value}`),
    );
    return entries;
  };

  const handleSubmit = event => {
    event.preventDefault();
    setSubmitting(true);
    if (inputs.submissionType === 'UPLOAD') {
      submitContentUpload(
        inputs.submissionType,
        inputs.contentId,
        inputs.contentType,
        inputs.contentRef.raw,
        packageMetadata(),
      ).then(() => {
        setSubmitting(false);
        setSubmittedId(inputs.contentId);
      });
    } else {
      submitContent(
        inputs.submissionType,
        inputs.contentId,
        inputs.contentType,
        inputs.contentRef,
        packageMetadata(),
      ).then(() => {
        setSubmitting(false);
        setSubmittedId(inputs.contentId);
      });
    }
  };

  return (
    <FixedWidthCenterAlignedLayout title="Submit Content">
      <Row>
        <Col>
          <Alert variant="secondary">
            <p>Provide content to the HMA system to match against.</p>
            <p>
              Currently only <b>images</b> using the submisson type{' '}
              <b>Direct Upload</b> or <b>URL</b> are supported.
            </p>
          </Alert>

          <Form onSubmit={handleSubmit}>
            <Form.Group>
              <Form.Label>Submission Type</Form.Label>
              <Form.Control
                as="select"
                required
                className="mr-sm-2"
                name="submissionType"
                onChange={e => {
                  setSubmissionType(SUBMISSION_TYPE[e.target.value]);
                  handleInputChange(e);
                }}
                defaultValue=""
                custom>
                <option key="empty" value="" disabled>
                  Select type...
                </option>
                {Object.keys(SUBMISSION_TYPE).map(submitType => (
                  <option key={submitType} value={submitType}>
                    {SUBMISSION_TYPE[submitType]}
                  </option>
                ))}
              </Form.Control>
            </Form.Group>

            <Form.Group className="mx-4">
              <Form.Row>
                {submissionType === SUBMISSION_TYPE.UPLOAD && (
                  <PhotoUploadField
                    inputs={inputs}
                    handleInputChangeUpload={handleInputChangeUpload}
                  />
                )}

                {submissionType === SUBMISSION_TYPE.URL && (
                  <Form.Group>
                    <Form.Label>Provide a URL to the content</Form.Label>
                    <Form.Control
                      onChange={handleInputChange}
                      name="contentRef"
                      placeholder="presigned url"
                      required
                    />
                    <Form.Text className="text-muted mt-0">
                      Currently behavior will store a copy of the content
                    </Form.Text>
                  </Form.Group>
                )}

                {submissionType === SUBMISSION_TYPE.RAW && (
                  <NotYetSupportedField
                    label="Provide content as raw string"
                    handleInputChange={handleInputChange}
                  />
                )}

                {submissionType === SUBMISSION_TYPE.S3_OBJECT && (
                  <NotYetSupportedField
                    label="Existing S3 Object Name"
                    handleInputChange={handleInputChange}
                  />
                )}
              </Form.Row>
              <ContentIdAndTypeField
                inputs={inputs}
                handleInputChange={handleInputChange}
              />
              <OptionalMetadataField
                submissionMetadata={submissionMetadata}
                setSubmissionMetadata={setSubmissionMetadata}
              />
              <Form.Group as={Row}>
                <Button
                  style={{maxHeight: 38}}
                  className="ml-3"
                  variant="primary"
                  disabled={
                    submitting ||
                    submissionType === SUBMISSION_TYPE.RAW ||
                    submissionType === SUBMISSION_TYPE.S3_OBJECT
                  }
                  type="submit">
                  Submit
                </Button>
                <Collapse in={submitting}>
                  <Spinner
                    as="span"
                    animation="border"
                    role="status"
                    variant="primary"
                  />
                </Collapse>
                <Collapse in={submittedId}>
                  <Col className="ml-4">
                    <Row>
                      Submitted! It will take a few minutes for the hash to be
                      generated.
                    </Row>
                    <Row>
                      <Link to={`/matches/${submittedId}`}>
                        Once created, the hash and any matches found can be
                        viewed here.
                      </Link>
                    </Row>
                  </Col>
                </Collapse>
              </Form.Group>
            </Form.Group>
          </Form>
        </Col>
      </Row>
    </FixedWidthCenterAlignedLayout>
  );
}
