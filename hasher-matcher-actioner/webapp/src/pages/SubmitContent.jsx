/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState} from 'react';
import {
  Col,
  Button,
  Row,
  Form,
  Container,
  InputGroup,
  Image,
  Collapse,
  Accordion,
  Card,
  Spinner,
} from 'react-bootstrap';
import {submitContent, submitContentUpload} from '../Api';

const SUBMISSION_TYPE = Object.freeze({
  UPLOAD: 'Direct Upload',
  RAW: 'Raw Value (example only)',
  S3_OBJECT: 'S3 Object (example only)',
  PRESIGNED_URL: 'Presigned URL (example only)',
});

const FORM_DEFUALTS = {
  submissionType: undefined,
  contentId: undefined,
  contentType: 'PHOTO',
  contentRef: undefined,
};

export default function SubmitContent() {
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [submissionType, setSubmissionType] = useState('');
  const [submissionMetadata, setSubmissionMetadata] = useState({});
  const [inputs, setInputs] = useState(FORM_DEFUALTS);

  const handleInputChange = event => {
    event.persist();
    setInputs(inputs_ => ({
      ...inputs_,
      [event.target.name]: event.target.value,
    }));
  };

  const handleInputChangeUpload = event => {
    const file = event.nativeEvent.path[0].files[0];
    setInputs(inputs_ => ({
      ...inputs_,
      [event.target.name]: {
        preview: URL.createObjectURL(file),
        raw: file,
      },
    }));
  };

  const packageMetadata = () => {
    const entries = [];
    Object.values(submissionMetadata).forEach(entry =>
      entries.push({[entry.key]: entry.value}),
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
        setSubmitted(true);
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
        setSubmitted(true);
      });
    }
  };

  return (
    <div className="d-flex flex-column justify-content-start align-items-stretch h-100 w-100">
      <div className="flex-grow-0">
        <Container className="bg-dark text-light" fluid>
          <Row className="d-flex flex-row justify-content-between align-items-end">
            <div className="px-4 py-2">
              <h1>Submit Content</h1>
              <p>Provide content to the HMA system to match against.</p>
            </div>
            <div className="px-4 py-2" />
          </Row>
        </Container>
      </div>
      <Container className="mt-4" style={{overflowY: 'auto'}}>
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
              {submissionType === SUBMISSION_TYPE.UPLOAD && (
                <Form.Group>
                  <Form.Label>Upload Photo</Form.Label>
                  <Form.File as={Col} custom required>
                    <Form.File.Label>
                      {inputs.contentRef &&
                      inputs.contentRef.raw &&
                      inputs.contentRef.raw instanceof File
                        ? inputs.contentRef.raw.name
                        : 'Submitted file will be stored by HMA System'}
                    </Form.File.Label>
                    <Form.File.Input
                      onChange={handleInputChangeUpload}
                      name="contentRef"
                    />
                  </Form.File>
                  <Form.Group>
                    {inputs.contentRef &&
                    inputs.contentRef.raw &&
                    inputs.contentRef.raw instanceof File ? (
                      <Accordion className="mt-3">
                        <Card>
                          <Card.Header>
                            <Accordion.Toggle
                              as={Button}
                              size="sm"
                              variant="link"
                              eventKey="0">
                              Preview
                            </Accordion.Toggle>
                          </Card.Header>
                          <Accordion.Collapse eventKey="0">
                            <Card.Body>
                              <Image
                                style={{
                                  border: 'none',
                                  maxHeight: '400px',
                                  maxWidth: '400px',
                                }}
                                src={
                                  inputs.contentRef && inputs.contentRef.preview
                                    ? inputs.contentRef.preview
                                    : ''
                                }
                                fluid
                                rounded
                              />
                            </Card.Body>
                          </Accordion.Collapse>
                        </Card>
                      </Accordion>
                    ) : undefined}
                  </Form.Group>
                </Form.Group>
              )}

              {submissionType === SUBMISSION_TYPE.RAW && (
                <Form.Group>
                  <Form.Label>Provide content as raw string</Form.Label>
                  <Form.Control
                    required
                    onChange={handleInputChange}
                    name="contentRef"
                    placeholder="Not Currently Supported"
                  />
                </Form.Group>
              )}

              {submissionType === SUBMISSION_TYPE.S3_OBJECT && (
                <Form.Group>
                  <Form.Label>Existing S3 Object Name</Form.Label>
                  <Form.Control
                    onChange={handleInputChange}
                    name="contentRef"
                    type="text"
                    placeholder="bucket_name/key"
                    required
                  />
                </Form.Group>
              )}

              {submissionType === SUBMISSION_TYPE.PRESIGNED_URL && (
                <Form.Group>
                  <Form.Label>{SUBMISSION_TYPE.PRESIGNED_URL}</Form.Label>
                  <Form.Control
                    onChange={handleInputChange}
                    name="contentRef"
                    placeholder={`Enter ${SUBMISSION_TYPE.PRESIGNED_URL}`}
                    required
                  />
                </Form.Group>
              )}
            </Form.Row>

            <Form.Row>
              <Form.Label>Content ID and Type</Form.Label>
              <InputGroup>
                <Form.Control
                  onChange={handleInputChange}
                  type="text"
                  name="contentId"
                  placeholder="Enter a unique identifier for content (currently behavior will overwrite)"
                  required
                />

                <Form.Group>
                  <Form.Control
                    onChange={handleInputChange}
                    required
                    as="select"
                    name="contentType"
                    custom>
                    <option key="empty" value="" hidden>
                      Select type...
                    </option>
                    <option key="1" value="PHOTO">
                      PHOTO
                    </option>
                  </Form.Control>
                </Form.Group>
              </InputGroup>
            </Form.Row>
            <Form.Row>
              <Form.Label as={Col}>Optional Metadata</Form.Label>

              <Form.Group>
                <Button
                  variant="success"
                  className="float-right mr-2"
                  size="sm"
                  onClick={() => {
                    setSubmissionMetadata({
                      ...submissionMetadata,
                      [Object.keys(submissionMetadata).length]: {},
                    });
                  }}>
                  +
                </Button>
              </Form.Group>
            </Form.Row>
            {Object.keys(submissionMetadata).map(entry => (
              <Form.Row key={entry}>
                <Form.Group as={Col}>
                  <InputGroup>
                    <InputGroup.Prepend>
                      <InputGroup.Text>Key</InputGroup.Text>
                    </InputGroup.Prepend>
                    <Form.Control
                      onChange={e => {
                        const metadataCopy = {...submissionMetadata};
                        metadataCopy[entry].key = e.target.value;
                        setSubmissionMetadata(metadataCopy);
                      }}
                    />
                  </InputGroup>
                </Form.Group>
                <Form.Group as={Col}>
                  <InputGroup>
                    <InputGroup.Prepend>
                      <InputGroup.Text>Value</InputGroup.Text>
                    </InputGroup.Prepend>
                    <Form.Control
                      onChange={e => {
                        const metadataCopy = {...submissionMetadata};
                        metadataCopy[entry].value = e.target.value;
                        setSubmissionMetadata(metadataCopy);
                      }}
                    />
                  </InputGroup>
                </Form.Group>
                <Form.Group>
                  <Button
                    variant="danger"
                    className="float-right"
                    onClick={() => {
                      const metadataCopy = {...submissionMetadata};
                      delete metadataCopy[entry];
                      setSubmissionMetadata(metadataCopy);
                    }}>
                    -
                  </Button>
                </Form.Group>
              </Form.Row>
            ))}
          </Form.Group>
          <Form.Group>
            <Button
              variant="primary"
              disabled={submitted || submissionType !== SUBMISSION_TYPE.UPLOAD}
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
            <Collapse in={submitted}>
              <span className="ml-2">Submitted!</span>
            </Collapse>
          </Form.Group>
        </Form>
      </Container>
    </div>
  );
}
