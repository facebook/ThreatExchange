/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React, {useState} from 'react';
import {Col, Button, Row, Form, Collapse, Spinner, Card} from 'react-bootstrap';
import {useHistory} from 'react-router-dom';

import {submitContentViaURL, submitContentViaPutURLUpload} from '../Api';
import {ContentType, SubmissionType} from '../utils/constants';

import {
  PhotoUploadField,
  OptionalAdditionalFields,
  AdditionalFields,
} from '../components/SubmitContentFields';
import FixedWidthCenterAlignedLayout from './layouts/FixedWidthCenterAlignedLayout';
import ChoiceCard from '../components/ChoiceCard';

const FORM_DEFAULTS = {
  submissionType: undefined,
  contentId: '',
  contentType: ContentType.Photo,
  content: '',
  force_resubmit: false,
};

export default function SubmitContent(): JSX.Element {
  const [submitting, setSubmitting] = useState(false);
  const [submittedId, setSubmittedId] = useState('');
  const [submissionError, setSubmissionError] = useState(false);
  const [submissionType, setSubmissionType] = useState('');
  const [additionalFields, setAdditionalFields] = useState<AdditionalFields>(
    {},
  );
  const [inputs, setInputs] = useState(FORM_DEFAULTS);
  const history = useHistory();

  // for most input changes we only need to take the input name and store the event value
  const handleInputChange = (e: React.SyntheticEvent) => {
    e.persist();
    const target = e.target as typeof e.target & {
      name: string;
      value: string;
    };
    setInputs(inputs_ => ({
      ...inputs_,
      [target.name]: target.value,
    }));
  };

  // image upload is a special case so that we can do the following:
  // - give a preview of the image to user
  // - auto populate the content id if it is currently empty
  const handleInputChangeUpload = (e: React.SyntheticEvent) => {
    const target = e.target as typeof e.target & {
      name: string;
      files: File[];
    };
    const file = target.files[0];
    const contentId = inputs.contentId ?? file.name;
    setInputs(inputs_ => ({
      ...inputs_,
      contentId,
      [target.name]: {
        preview: URL.createObjectURL(file),
        raw: file,
      },
    }));
  };

  const packageAdditionalFields = () => {
    const entries = [] as string[];
    Object.values(additionalFields).forEach(entry =>
      // TODO extra additional fields spec should be established in documentation
      entries.push(`${entry.value}`),
    );
    return entries;
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setSubmissionError(false);
    if (inputs.content === undefined) {
      return;
    }

    if (inputs.submissionType === 'PUT_URL_UPLOAD') {
      submitContentViaPutURLUpload(
        inputs.contentId,
        inputs.contentType,
        packageAdditionalFields(),
        (inputs.content as unknown as {raw: File}).raw,
        inputs.force_resubmit,
      )
        .then(() => {
          setSubmitting(false);
          setSubmittedId(inputs.contentId);
        })
        .catch(() => {
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
        .catch(() => {
          setSubmitting(false);
          setSubmissionError(true);
        });
    }
  };

  const handleSubmitAnother = () => {
    // Does not change submission type, clears out additional fields. Depending
    // on feedback we may want to keep additional fields at their current
    // values.
    setSubmittedId('');
    setSubmitting(false);
    setAdditionalFields({});
    setInputs(FORM_DEFAULTS);
  };

  return (
    <FixedWidthCenterAlignedLayout title="Submit Content">
      <Row>
        <Col>
          <Form className="hma-themed-form" onSubmit={handleSubmit}>
            <Form.Group>
              <Form.Label>Content Type</Form.Label>
              <Row>
                <Col xs="6">
                  <ChoiceCard
                    label="Photo"
                    description="Submit photo or other image."
                    selected={inputs.contentType === ContentType.Photo}
                    onSelect={() =>
                      setInputs({...inputs, contentType: ContentType.Photo})
                    }
                  />
                </Col>
                <Col xs="6">
                  <ChoiceCard
                    label="Video"
                    description="Submit video or gif."
                    selected={inputs.contentType === ContentType.Video}
                    onSelect={() =>
                      setInputs({...inputs, contentType: ContentType.Video})
                    }
                  />
                </Col>
              </Row>
            </Form.Group>
            <Form.Group>
              <Form.Label>Submission Method</Form.Label>
              <Form.Control
                as="select"
                required
                className="mr-sm-2"
                name="submissionType"
                onChange={(e: React.FormEvent) => {
                  const target = e.target as typeof e.target & {
                    value: keyof typeof SubmissionType;
                  };
                  setSubmissionType(SubmissionType[target.value]);
                  handleInputChange(e);
                }}
                defaultValue=""
                custom>
                <option key="empty" value="" disabled>
                  Select type...
                </option>
                {Object.keys(SubmissionType).map(submitType => (
                  <option key={submitType} value={submitType}>
                    {SubmissionType[submitType as keyof typeof SubmissionType]}
                  </option>
                ))}
              </Form.Control>
            </Form.Group>

            {submissionType === SubmissionType.FROM_URL && (
              <Form.Group>
                <Form.Label>Provide a URL to the content</Form.Label>
                <Form.Control
                  onChange={handleInputChange}
                  name="content"
                  placeholder="url to content"
                  required
                  value={inputs.content}
                />
                <Form.Text className="text-muted mt-0">
                  Currently behavior will store a copy of the content
                </Form.Text>
              </Form.Group>
            )}

            {submissionType === SubmissionType.PUT_URL_UPLOAD && (
              <Form.Group>
                <PhotoUploadField
                  inputs={inputs}
                  handleInputChange={handleInputChangeUpload}
                />
              </Form.Group>
            )}

            <Form.Group>
              <Form.Group>
                <Form.Label>Unique ID for Content</Form.Label>
                <Form.Control
                  onChange={handleInputChange}
                  type="text"
                  name="contentId"
                  placeholder="Enter a unique identifier for content"
                  required
                  value={inputs.contentId}
                />

                <Form.Text className="text-muted mt-0">
                  Warning currently behavior will overwrite content with the
                  same id
                </Form.Text>
              </Form.Group>
            </Form.Group>
            <OptionalAdditionalFields
              additionalFields={additionalFields}
              setAdditionalFields={setAdditionalFields}
            />
            <Form.Group>
              <Form.Check
                disabled={submitting || submittedId !== ''}
                name="force_resubmit"
                inline
                label="Resubmit if content id already present in system"
                type="checkbox"
                onChange={handleInputChange}
              />
              <Form.Text className="text-muted mt-0">
                Be careful submitting different content with the same id is not
                supported and will likely error.
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
              <Collapse in={submittedId !== ''}>
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
                      <Button variant="secondary" onClick={handleSubmitAnother}>
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
          </Form>
        </Col>
      </Row>
    </FixedWidthCenterAlignedLayout>
  );
}
