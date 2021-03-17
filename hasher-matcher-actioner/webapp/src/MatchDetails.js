/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, { useState } from 'react';
import { useHistory, useParams } from 'react-router-dom';
import { Button, Col, Collapse, Image, Row } from 'react-bootstrap';

export default function MatchDetails() {
  let history = useHistory();
  let { id } = useParams();
  const [ showNewReactionButtons, setShowNewReactionButtons ] = useState(false);
  const [ reaction, setReaction ] = useState('Seen');
  return (
    <>
      <button className="float-right btn btn-primary" onClick={() => history.goBack()}>Back</button>
      <h1>Match Details</h1>
      <Row>
        <Col md={6}>
          <table class="table">
            <tr><td>Matched content:</td><td>{id}</td></tr>
            <tr><td>Matched on:</td><td>2 Feb 2021 5:03am</td></tr>
            <tr><td>Reaction:</td>
              <td>
  {reaction} <Button className="float-right" size="sm" variant="outline-primary" onClick={() => setShowNewReactionButtons(!showNewReactionButtons)}>{showNewReactionButtons?'Cancel':'Change'}</Button>
                <Collapse in={showNewReactionButtons}>
                  <div>
                    <p class="mt-3">Change reaction to...</p>
                    <Button size="sm" variant="outline-primary" onClick={() => {
                      setReaction('Positive');
                      setShowNewReactionButtons(false);
                    }}>Positive</Button>
                    <Button className="ml-2" size="sm" variant="outline-primary">False Positive</Button>
                  </div>
                </Collapse>
              </td>
            </tr>
          </table>
        </Col>
        <Col md={6}>
          <Image src="https://www.creditabsolute.com/wp-content/uploads/2019/04/block_beach_1.jpg" fluid={true} rounded={true} />
        </Col>
      </Row>
      <Row>
        <Col md={12}>
          <table class="table mt-4">
            <thead>
              <tr>
                <th>ID</th>
                <th>Indicator Type</th>
                <th>Indicator</th>
                <th>Created</th>
                <th>Last Updated</th>
                <th>Tags</th>
                <th>Status</th>
                <th>Partners with Opinions</th>
                <th>Action Taken</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>2880742865368386</td>
                <td>HASH_PDQ</td>
                <td style={{maxWidth: "250px", overflow: "hidden"}}><span style={{overflow: "hidden"}}></span>acecf3355e3125c8e24e2f30e0d4ec4f8482b878b3c34cdbdf063278db275992</td>
                <td>31 Jul 2020 6:47pm</td>
                <td>31 Jul 2020 6:47pm</td>
                <td>tag1, tag2</td>
                <td>MALICIOUS</td>
                <td>app1, app2</td>
                <td>Delete</td>
              </tr>
            </tbody>
          </table>
        </Col>
      </Row>
    </>
  );
}
