/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState} from 'react';
import {Link} from 'react-router-dom';
import {Button, Col, Collapse, Image, Row} from 'react-bootstrap';
import Spinner from 'react-bootstrap/Spinner';

import {uploadImage} from './Api';

export default function Upload() {
  const [fileName, setFileName] = useState('Select Browse to choose a file.');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [image, setImage] = useState({preview: '', raw: ''});

  return (
    <>
      <h1>Upload</h1>
      <Row className="mt-3" float>
        <Col md={6}>
          Checkout WIP{' '}
          <Link as="Button" to="/submit">
            Submit Page
          </Link>{' '}
          that will soon replace this one!
        </Col>
      </Row>
      <Row className="mt-3">
        <Col md={6}>
          <Collapse in={!submitting && !submitted}>
            <div>
              <p>
                Browse then select a file to upload for hashing, matching and
                actioning, then select <strong>Submit</strong>.
              </p>
              <div className="custom-file">
                <input
                  type="file"
                  className="custom-file-input"
                  id="customFile"
                  onChange={e => {
                    const file = e.nativeEvent.path[0].files[0];
                    setFileName(file.name);
                    setImage({
                      preview: URL.createObjectURL(file),
                      raw: file,
                    });
                  }}
                />
                <label className="custom-file-label" htmlFor="customFile">
                  {fileName}
                </label>
              </div>
              <div className="mt-3">
                <Button
                  onClick={() => {
                    setSubmitting(true);
                    // TODO check for succesfull upload
                    uploadImage(image.raw).then(() => {
                      setSubmitted(true);
                      setSubmitting(false);
                    });
                  }}>
                  Submit
                </Button>
              </div>
            </div>
          </Collapse>
          <Collapse in={submitting}>
            <div>
              <p>Please wait. Attempting to upload image.</p>
              <Spinner animation="border" role="status">
                <span className="sr-only">Loading...</span>
              </Spinner>
            </div>
          </Collapse>
          {/* TODO this should poll the API for results */}
          <Collapse in={submitted}>
            <div>
              <p>Uploaded {fileName}: hash should be generated shortly... </p>
              <p> if a match is found it will be visible here: </p>
              <p>
                <Link as={Button} to={`/matches/${fileName}`}>
                  View Match Details
                </Link>
              </p>
            </div>
          </Collapse>
        </Col>
        <Col md={6}>
          <Collapse in={fileName !== 'Select Browse to choose a file.'}>
            <Image src={image.preview} fluid rounded />
          </Collapse>
        </Col>
      </Row>
    </>
  );
}
