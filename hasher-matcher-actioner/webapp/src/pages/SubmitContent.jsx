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
  Card,
} from 'react-bootstrap';
import {useHistory} from 'react-router-dom';

import {submitContentViaURL, submitContentViaPutURLUpload} from '../Api';
import {ContentType, SUBMISSION_TYPE} from '../utils/constants';

import {
  ContentUniqueIdField,
  PhotoUploadField,
  OptionalAdditionalFields,
} from '../components/SubmitContentFields';
import FixedWidthCenterAlignedLayout from './layouts/FixedWidthCenterAlignedLayout';

const FORM_DEFAULTS = {
  submissionType: undefined,
  contentId: '',
  contentType: ContentType.Photo,
  content: undefined,
  force_resubmit: false,
};

export default function SubmitContent() {
  const [submitting, setSubmitting] = useState(false);
  const [submittedId, setSubmittedId] = useState(undefined);
  const [submissionError, setSubmissionError] = useState(undefined);
  const [submissionType, setSubmissionType] = useState('');
  const [additionalFields, setAdditionalFields] = useState({});
  const [inputs, setInputs] = useState(FORM_DEFAULTS);
  const history = useHistory();

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
    const file = event.target.files[0];
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

  const packageAdditionalFields = () => {
    const entries = [];
    Object.values(additionalFields).forEach(entry =>
      // TODO extra additional fields spec should be established in documentation
      entries.push(`${entry.value}`),
    );
    return entries;
  };

  const handleSubmit = event => {
    event.preventDefault();
    setSubmitting(true);
    setSubmissionError(false);
    if (inputs.submissionType === 'PUT_URL_UPLOAD') {
      submitContentViaPutURLUpload(
        inputs.contentId,
        inputs.contentType,
        packageAdditionalFields(),
        inputs.content.raw,
        inputs.force_resubmit,
      )
        .then(() => {
          setSubmitting(false);
          setSubmittedId(inputs.contentId);
        })
        .catch(error => {
          setSubmitting(false);
          setSubmissionError(true);
        });
    } else {
      submitContentViaURL(
        inputs.contentId,
        inputs.contentType,
        packageAdditionalFields(),
        inputs.content,
        inputs.force_resubmit,
      )
        .then(() => {
          setSubmitting(false);
          setSubmittedId(inputs.contentId);
        })
        .catch(error => {
          setSubmitting(false);
          setSubmissionError(true);
        });
    }
  };

  const handleSubmitAnother = event => {
    // Does not change submission type, clears out additional fields. Depending
    // on feedback we may want to keep additional fields at their current
    // values.
    setSubmittedId(undefined);
    setSubmitting(false);
    setAdditionalFields({});
    setInputs(FORM_DEFAULTS);
  };

  return (
    <FixedWidthCenterAlignedLayout title="Submit Content">
      <Row>
        <Col>
          <Alert variant="secondary">
            <p>Provide content to the HMA system to match against.</p>
            <p>
              Currently only <b>images</b> using the submisson type{' '}
              <b>Upload</b> or <b>URL</b> are supported.{' '}
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

            <Form.Group>
              <Form.Row>
                {submissionType === SUBMISSION_TYPE.FROM_URL && (
                  <Form.Group>
                    <Form.Label>Provide a URL to the content</Form.Label>
                    <Form.Control
                      onChange={handleInputChange}
                      name="content"
                      placeholder="url to content"
                      required
                    />
                    <Form.Text className="text-muted mt-0">
                      Currently behavior will store a copy of the content
                    </Form.Text>
                  </Form.Group>
                )}

                {submissionType === SUBMISSION_TYPE.PUT_URL_UPLOAD && (
                  <PhotoUploadField
                    inputs={inputs}
                    handleInputChangeUpload={handleInputChangeUpload}
                  />
                )}
              </Form.Row>
              <ContentUniqueIdField
                inputs={inputs}
                handleInputChange={handleInputChange}
              />
              <OptionalAdditionalFields
                additionalFields={additionalFields}
                setAdditionalFields={setAdditionalFields}
              />
              <Form.Group>
                <Form.Row>
                  <Form.Check
                    disabled={submitting || submittedId}
                    name="force_resubmit"
                    inline
                    label="Resubmit if content id already present in system"
                    type="checkbox"
                    onChange={handleInputChange}
                  />
                </Form.Row>
                <Form.Text className="text-muted mt-0">
                  Be careful submitting different content with the same id is
                  not supported and will likely error.
                </Form.Text>
              </Form.Group>
              <Form.Group as={Row}>
                <Collapse in={submitting}>
                  <Spinner
                    as="span"
                    animation="border"
                    role="status"
                    variant="primary"
                  />
                </Collapse>
                <Collapse in={!submittedId}>
                  <Button
                    style={{maxHeight: 38}}
                    className="ml-3"
                    variant="primary"
                    disabled={submitting}
                    type="submit">
                    Submit
                  </Button>
                </Collapse>
                <Collapse in={submittedId}>
                  <Col>
                    <Card>
                      <Card.Header>Your content is submitted!</Card.Header>
                      <Card.Body>
                        <Button
                          variant="primary"
                          onClick={() =>
                            history.push(`/pipeline-progress/${submittedId}`)
                          }>
                          Track Submission
                        </Button>{' '}
                        <Button
                          variant="secondary"
                          onClick={handleSubmitAnother}>
                          Submit Another
                        </Button>
                      </Card.Body>
                    </Card>
                  </Col>
                </Collapse>
                <Collapse in={submissionError}>
                  <Col className="ml-4">
                    <Card border="danger">
                      <Card.Header>Error when submitting.</Card.Header>
                      <Card.Body>
                        Error submitting. This can occur if content with that id
                        already exists.
                      </Card.Body>
                    </Card>
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
