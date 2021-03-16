/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button, Collapse, Modal } from 'react-bootstrap'

export default function Matches() {
  const [showFilters, setShowFilters] = useState(false);
  const [showModal, setShowModal] = useState(false);
  return (
    <>
      <button className="float-right btn btn-primary" onClick={() => setShowFilters(!showFilters)}>{showFilters ? 'Hide' : 'Show'} Filters</button>
      <h1>Matches</h1>
      <Collapse in={showFilters}>
        <div>
          <form>
            <div class="row mt-3">
              <div class="col-md-6 form-group">
                <label htmlFor="from">From</label>
                <input id="from" type="text" class="form-control" placeholder="mm/dd/yyyy hh:mm:ss" />
              </div>
              <div class="col-md-6 form-group">
                <label htmlFor="to">To</label>
                <input id="to" type="text" class="form-control" placeholder="mm/dd/yyyy hh:mm:ss" />
              </div>
              <div class="col-md-6 form-group">
                <label htmlFor="image">Image</label>
                <input id="image" type="text" class="form-control" />
              </div>
              <div class="col-md-6 form-group">
                <label htmlFor="hash">Hash</label>
                <input id="hash" type="text" class="form-control" />
              </div>
              <div class="col-md-6 form-group">
                <label htmlFor="signal-type">Signal Type</label>
                <select id="signal-type" class="form-control">
                  <option>Signal Source 1 &mdash; All Data Types</option>
                  <option>Signal Source 1 &mdash; HASH_PDQ</option>
                  <option>Signal Source 1 &mdash; HASH_PDQ_OCR</option>
                  <option>Signal Source 2 &mdash; All Data Types</option>
                  <option>Signal Source 2 &mdash; DEBUG_STRING</option>
                  <option>Signal Source 2 &mdash; HASH_PDQ</option>
                  <option>Signal Source 2 &mdash; HASH_PDQ_OCR</option>
                </select>
              </div>
            </div>
            <div class="text-right mb-4">
              <button class="btn btn-secondary">Clear</button>
              <button class="btn btn-primary ml-2">Apply</button>
            </div>
          </form>
        </div>
      </Collapse>
      <div class="row mt-3">
        <div class="col-xs-12">
          <table class="table table-hover table-sm">
            <thead>
              <tr>
                <th>Image</th>
                <th>Hash</th>
                <th>Matched On</th>
                <th>Reaction</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr class="align-middle">
                <td class="align-middle">file1.jpg</td>
                <td class="align-middle">8a551807446ba95400eb032ba8fe51c3857eaaa5570cea70bb87775cbdc1eebe</td>
                <td class="align-middle">5 Feb 2021 1:47pm</td>
                <td class="align-middle">Seen</td>
                <td class="align-middle"><button class="btn btn-outline-primary btn-sm" onClick={() => setShowModal(true)}>Details</button></td>
              </tr>
              <tr>
                <td class="align-middle">file1.jpg</td>
                <td class="align-middle">652fe95ab4ae5129c07e92da787e525ab44b736ea5ab5ce4485ba344158b8e86</td>
                <td class="align-middle">5 Feb 2021 1:44pm</td>
                <td class="align-middle">Seen</td>
                <td class="align-middle"><Link to="/matches/file1.jpg" class="btn btn-outline-primary btn-sm">Details</Link></td>
              </tr>
              <tr>
                <td class="align-middle">file2.jpg</td>
                <td class="align-middle">652fe95ab4ae5129c07e92da787e525ab44b736ea5ab5ce4485ba344158b8e86</td>
                <td class="align-middle">5 Feb 2021 1:44pm</td>
                <td class="align-middle">Positive</td>
                <td class="align-middle"><button class="btn btn-outline-primary btn-sm">Details</button></td>
              </tr>
              <tr>
                <td class="align-middle">file3.jpg</td>
                <td class="align-middle">652fe95ab4ae5129c07e92da787e525ab44b736ea5ab5ce4485ba344158b8e86</td>
                <td class="align-middle">5 Feb 2021 1:44pm</td>
                <td class="align-middle">Positive</td>
                <td class="align-middle"><button class="btn btn-outline-primary btn-sm">Details</button></td>
              </tr>
              <tr>
                <td class="align-middle">file4.jpg</td>
                <td class="align-middle">652fe95ab4ae5129c07e92da787e525ab44b736ea5ab5ce4485ba344158b8e86</td>
                <td class="align-middle">5 Feb 2021 1:44pm</td>
                <td class="align-middle">False Positive</td>
                <td class="align-middle"><button class="btn btn-outline-primary btn-sm">Details</button></td>
              </tr>
              <tr>
                <td class="align-middle">file5.jpg</td>
                <td class="align-middle">652fe95ab4ae5129c07e92da787e525ab44b736ea5ab5ce4485ba344158b8e86</td>
                <td class="align-middle">5 Feb 2021 1:44pm</td>
                <td class="align-middle">Seen</td>
                <td class="align-middle"><button class="btn btn-outline-primary btn-sm">Details</button></td>
              </tr>
              <tr>
                <td class="align-middle">file6.jpg</td>
                <td class="align-middle">652fe95ab4ae5129c07e92da787e525ab44b736ea5ab5ce4485ba344158b8e86</td>
                <td class="align-middle">5 Feb 2021 1:44pm</td>
                <td class="align-middle">Positive</td>
                <td class="align-middle"><button class="btn btn-outline-primary btn-sm">Details</button></td>
              </tr>
              <tr>
                <td class="align-middle">file7.jpg</td>
                <td class="align-middle">652fe95ab4ae5129c07e92da787e525ab44b736ea5ab5ce4485ba344158b8e86</td>
                <td class="align-middle">5 Feb 2021 1:44pm</td>
                <td class="align-middle">Seen</td>
                <td class="align-middle"><button class="btn btn-outline-primary btn-sm">Details</button></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <MatchDetailsModal show={showModal} onHide={() => setShowModal(false)} />
    </>
  );
}

function MatchDetailsModal(props) {
  return (
    <Modal
      {...props}
      size="lg"
      aria-labelledby="contained-modal-title-vcenter"
      centered
    >
      <Modal.Header closeButton>
        <Modal.Title id="contained-modal-title-vcenter">
          Match Details
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <h4>Centered Modal</h4>
        <p>
          Cras mattis consectetur purus sit amet fermentum. Cras justo odio,
          dapibus ac facilisis in, egestas eget quam. Morbi leo risus, porta ac
          consectetur ac, vestibulum at eros.
        </p>
      </Modal.Body>
      <Modal.Footer>
        <Button onClick={props.onHide}>Close</Button>
      </Modal.Footer>
    </Modal>
  );
}
