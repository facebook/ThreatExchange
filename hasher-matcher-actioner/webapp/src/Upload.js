/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button, Col, Collapse, Image, Row } from 'react-bootstrap';
import Spinner from 'react-bootstrap/Spinner';

export default function Upload() {
  const [ fileName, setFileName ] = useState('Select Browse to choose a file.');
  const [ submitting, setSubmitting ] = useState(false);
  const [ submitted, setSubmitted ] = useState(false);
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
              }} />
              <label className="custom-file-label" for="customFile">{fileName}</label>
            </div>
            <div className="mt-3">
              <Button onClick={() => {
                setSubmitting(true);
                setTimeout(() => {
                  setSubmitted(true);
                  setSubmitting(false);
                }, 3000);
              }}>Submit</Button>
            </div>
            </div>
          </Collapse>
          <Collapse in={submitting}>
            <div>
              <p>
                Please wait. It may take several seconds to hash and check for matches.
              </p>
              <Spinner animation="border" role="status" >
                <span className="sr-only">Loading...</span>
              </Spinner>
            </div>
          </Collapse>
          <Collapse in={submitted}>
            <div>
              <p>Hash created for {fileName}: acecf3355e3125c8e24e2f30e0d4ec4f8482b878b3c34cdbdf063278db275992</p>
              <p>...either this...</p>
              <p>{fileName} does not match any signals.</p>
              <p>...or this...</p>
              <p>{fileName} matches one or more signals.</p>
              <p><Link as={Button} to={'/matches/' + fileName}>View Match Details</Link></p>
            </div>
          </Collapse>
        </Col>
        <Col md={6}>
          <Collapse in={fileName !== 'Select Browse to choose a file.'}>
            <Image src="https://www.creditabsolute.com/wp-content/uploads/2019/04/block_beach_1.jpg" fluid={true} rounded={true} />
          </Collapse>
        </Col>
      </Row>
    </>
  );
}
