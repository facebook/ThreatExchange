/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
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

import {SubmissionType} from '../utils/constants';

type Inputs = {
  submissionType?: SubmissionType;
  contentId: string;
  contentType: string;
  content: string | {raw: File; preview: string};
};

type ContentFieldProps = {
  inputs: Inputs;
  handleInputChange: (e: React.SyntheticEvent) => void;
};

export function PhotoUploadField({
  inputs,
  handleInputChange,
}: ContentFieldProps): JSX.Element {
  const content = inputs.content as {raw: File; preview: string};
  const fileNameIfExist = () =>
    content && content.raw && content.raw instanceof File
      ? content.raw.name
      : undefined;

  return (
    <Form.Group>
      <Form.Label>Upload Photo</Form.Label>
      <Form.File as={Col} custom required>
        <Form.File.Label>
          {fileNameIfExist() ?? 'Submitted file will be stored by HMA System'}
        </Form.File.Label>
        <Form.File.Input onChange={handleInputChange} name="content" />
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
                    src={fileNameIfExist() ? content.preview : ''}
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

export type AdditionalFields = {[key: string]: {value: string}};

type OptionalAdditionalFieldsProps = {
  additionalFields: AdditionalFields;
  setAdditionalFields: (additionalFields: AdditionalFields) => void;
};

export function OptionalAdditionalFields({
  additionalFields,
  setAdditionalFields,
}: OptionalAdditionalFieldsProps): JSX.Element {
  return (
    <Form.Group>
      <Form.Row>
        <Form.Label>Optional Additional Fields</Form.Label>
      </Form.Row>
      {Object.keys(additionalFields).map(entry => (
        <Form.Row key={entry}>
          <Form.Group as={Col}>
            <InputGroup>
              <InputGroup.Prepend>
                <InputGroup.Text>Field</InputGroup.Text>
              </InputGroup.Prepend>
              <Form.Control
                onChange={(e: React.FormEvent) => {
                  const target = e.target as typeof e.target & {
                    value: string;
                  };
                  const copy = {...additionalFields};
                  copy[entry].value = target.value;
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
