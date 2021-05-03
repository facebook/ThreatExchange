/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';
import {
  Col,
  Button,
  Form,
  InputGroup,
  Image,
  Accordion,
  Card,
} from 'react-bootstrap';
import PropTypes from 'prop-types';

import {SUBMISSION_TYPE} from '../utils/constants';

const inputsShape = {
  submissionType: PropTypes.oneOf(Object.keys(SUBMISSION_TYPE)),
  contentId: PropTypes.string,
  contentType: PropTypes.string,
  contentRef: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.shape({raw: PropTypes.file, preview: PropTypes.string}),
  ]),
};

export function ContentIdAndTypeField({inputs, handleInputChange}) {
  return (
    <Form.Group>
      <Form.Row>
        <Form.Label>Content ID and Type</Form.Label>
        <InputGroup>
          <Form.Control
            onChange={handleInputChange}
            type="text"
            name="contentId"
            placeholder="Enter a unique identifier for content"
            required
            value={inputs.contentId}
          />

          <Form.Group className="mb-0">
            <Form.Control
              onChange={handleInputChange}
              required
              as="select"
              name="contentType"
              defaultValue="PHOTO"
              custom>
              {/* (defaults to photo for now) */}
              <option key="empty" value="" hidden>
                Select content type...
              </option>
              <option key="1" value="PHOTO">
                PHOTO
              </option>
            </Form.Control>
          </Form.Group>
        </InputGroup>
      </Form.Row>
      <Form.Text className="text-muted mt-0">
        Warning currently behavior will overwrite content with the same id
      </Form.Text>
    </Form.Group>
  );
}

ContentIdAndTypeField.propTypes = {
  inputs: PropTypes.shape(inputsShape),
  handleInputChange: PropTypes.func.isRequired,
};

ContentIdAndTypeField.defaultProps = {
  inputs: undefined,
};

export function PhotoUploadField({inputs, handleInputChangeUpload}) {
  const fileNameIfExist = () =>
    inputs.contentRef &&
    inputs.contentRef.raw &&
    inputs.contentRef.raw instanceof File
      ? inputs.contentRef.raw.name
      : undefined;

  return (
    <Form.Group>
      <Form.Label>Upload Photo</Form.Label>
      <Form.File as={Col} custom required>
        <Form.File.Label>
          {fileNameIfExist() ?? 'Submitted file will be stored by HMA System'}
        </Form.File.Label>
        <Form.File.Input onChange={handleInputChangeUpload} name="contentRef" />
      </Form.File>
      <Form.Group>
        {fileNameIfExist() ? (
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
                    src={fileNameIfExist() ? inputs.contentRef.preview : ''}
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
  );
}

PhotoUploadField.propTypes = {
  inputs: PropTypes.shape(inputsShape),
  handleInputChangeUpload: PropTypes.func.isRequired,
};

PhotoUploadField.defaultProps = {
  inputs: undefined,
};

export function OptionalMetadataField({
  submissionMetadata,
  setSubmissionMetadata,
}) {
  return (
    <Form.Group>
      <Form.Row>
        <Form.Label as={Col}>Optional Metadata (not recorded yet)</Form.Label>
        <Form.Group>
          <Button
            variant="success"
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
  );
}

OptionalMetadataField.propTypes = {
  submissionMetadata: PropTypes.objectOf(PropTypes.string),
  setSubmissionMetadata: PropTypes.func.isRequired,
};

OptionalMetadataField.defaultProps = {
  submissionMetadata: undefined,
};

export function NotYetSupportedField({label, handleInputChange}) {
  return (
    <Form.Group>
      <Form.Label>{label}</Form.Label>
      <Form.Control
        onChange={handleInputChange}
        name="contentRef"
        placeholder="Not yet supported"
        required
      />
    </Form.Group>
  );
}

NotYetSupportedField.propTypes = {
  label: PropTypes.string,
  handleInputChange: PropTypes.func.isRequired,
};

NotYetSupportedField.defaultProps = {
  label: undefined,
};
