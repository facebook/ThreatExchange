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
  content: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.shape({raw: PropTypes.file, preview: PropTypes.string}),
  ]),
};

export function ContentUniqueIdField({inputs, handleInputChange}) {
  return (
    <Form.Group>
      <Form.Row>
        <Form.Label>Unique ID for Content</Form.Label>
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
              value={inputs.contentType}
              custom>
              {/* (defaults to photo for now) */}
              <option key="empty" value="" hidden>
                Select content type...
              </option>
              {/* TODO: Use an enum here. */}
              <option key="1" value="photo">
                Photo
              </option>
              <option key="2" value="video">
                Video
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

ContentUniqueIdField.propTypes = {
  inputs: PropTypes.shape(inputsShape),
  handleInputChange: PropTypes.func.isRequired,
};

ContentUniqueIdField.defaultProps = {
  inputs: undefined,
};

export function PhotoUploadField({inputs, handleInputChangeUpload}) {
  const fileNameIfExist = () =>
    inputs.content && inputs.content.raw && inputs.content.raw instanceof File
      ? inputs.content.raw.name
      : undefined;

  return (
    <Form.Group>
      <Form.Label>Upload Photo</Form.Label>
      <Form.File as={Col} custom required>
        <Form.File.Label>
          {fileNameIfExist() ?? 'Submitted file will be stored by HMA System'}
        </Form.File.Label>
        <Form.File.Input onChange={handleInputChangeUpload} name="content" />
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
                    src={fileNameIfExist() ? inputs.content.preview : ''}
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

export function OptionalAdditionalFields({
  additionalFields,
  setAdditionalFields,
}) {
  return (
    <Form.Group>
      <Form.Row>
        <Form.Label as={Col}>Optional Additional Fields</Form.Label>
      </Form.Row>
      {Object.keys(additionalFields).map(entry => (
        <Form.Row key={entry}>
          <Form.Group as={Col}>
            <InputGroup>
              <InputGroup.Prepend>
                <InputGroup.Text>Field</InputGroup.Text>
              </InputGroup.Prepend>
              <Form.Control
                onChange={e => {
                  const copy = {...additionalFields};
                  copy[entry].value = e.target.value;
                  setAdditionalFields(copy);
                }}
              />
            </InputGroup>
          </Form.Group>
          <Form.Group>
            <Button
              variant="danger"
              className="float-right"
              onClick={() => {
                const copy = {...additionalFields};
                delete copy[entry];
                setAdditionalFields(copy);
              }}>
              -
            </Button>
          </Form.Group>
        </Form.Row>
      ))}
      <Form.Group>
        <Button
          variant="success"
          onClick={() => {
            setAdditionalFields({
              ...additionalFields,
              [Object.keys(additionalFields).length]: {},
            });
          }}>
          +
        </Button>
      </Form.Group>
    </Form.Group>
  );
}

OptionalAdditionalFields.propTypes = {
  additionalFields: PropTypes.objectOf(PropTypes.string),
  setAdditionalFields: PropTypes.func.isRequired,
};

OptionalAdditionalFields.defaultProps = {
  additionalFields: undefined,
};

export function NotYetSupportedField({label, handleInputChange}) {
  return (
    <Form.Group>
      <Form.Label>{label}</Form.Label>
      <Form.Control
        onChange={handleInputChange}
        name="content"
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
