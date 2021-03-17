/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button, Col, Collapse, Image, Row } from 'react-bootstrap';
import Spinner from 'react-bootstrap/Spinner';

import { postAPI } from './Api'

export default function Upload() {
  const [fileName, setFileName] = useState('Select Browse to choose a file.');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [image, setImage] = useState({ preview: "", raw: "" });

  function handleUpload() {
    const formData = new FormData();
    formData.append("image", image.raw);
    postAPI('upload', formData).then((response) => {
      // TODO check for succesfull upload
      setSubmitted(true);
      setSubmitting(false)
    })
  }

  return (
    <>
      <h1>Upload</h1>
      <Row className="mt-3">
        <Col md={6}>
          <Collapse in={!submitting && !submitted}>
            <div>
              <p>
                Browse then select a file to upload for hashing, matching and actioning, then select <strong>Submit</strong>.
            </p>
              <div className="custom-file">
                <input type="file" className="custom-file-input" id="customFile" onChange={(e) => {
                  setFileName(e.nativeEvent.path[0].files[0].name);
                  setImage({
                    preview: URL.createObjectURL(e.nativeEvent.path[0].files[0]),
                    raw: e.nativeEvent.path[0].files[0]
                  }
                  );
                }} />
                <label className="custom-file-label" for="customFile">{fileName}</label>
              </div>
              <div className="mt-3">
                <Button onClick={() => {
                  setSubmitting(true);
                  handleUpload()
                }}>Submit</Button>
              </div>
            </div>
          </Collapse>
          <Collapse in={submitting}>
            <div>
              <p>
                Please wait. Attempting to upload image.
              </p>
              <Spinner animation="border" role="status" >
                <span className="sr-only">Loading...</span>
              </Spinner>
            </div>
          </Collapse>
          <Collapse in={submitted}>
            <div>
              <p>Uploaded {fileName}: hash should be generated shortly... </p>
              <p> if a match is found it will be visable here: </p>
              <p><Link as={Button} to={'/matches/' + fileName}>View Match Details</Link></p>
            </div>
          </Collapse>
        </Col>
        <Col md={6}>
          <Collapse in={fileName !== 'Select Browse to choose a file.'}>
            <Image src={image.preview} fluid={true} rounded={true} />
          </Collapse>
        </Col>
      </Row>
    </>
  );
}
