/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState, useEffect} from 'react';
import {Link} from 'react-router-dom';
import {Button, Collapse, Modal} from 'react-bootstrap';
import Spinner from 'react-bootstrap/Spinner';

import {fetchMatches} from './Api';

export default function Matches() {
  const [showFilters, setShowFilters] = useState(false);
  const [showModal, setShowModal] = useState(false);
  return (
    <>
      <button
        type="submit"
        className="float-right btn btn-primary"
        onClick={() => setShowFilters(!showFilters)}>
        {showFilters ? 'Hide' : 'Show'} Filters
      </button>
      <h1>Matches</h1>
      <Collapse in={showFilters}>
        <div>
          <form>
            <div className="row mt-3">
              <div className="col-md-6 form-group">
                <label htmlFor="from">From</label>
                <input
                  id="from"
                  type="text"
                  className="form-control"
                  placeholder="mm/dd/yyyy hh:mm:ss"
                />
              </div>
              <div className="col-md-6 form-group">
                <label htmlFor="to">To</label>
                <input
                  id="to"
                  type="text"
                  className="form-control"
                  placeholder="mm/dd/yyyy hh:mm:ss"
                />
              </div>
              <div className="col-md-6 form-group">
                <label htmlFor="image">Image</label>
                <input id="image" type="text" className="form-control" />
              </div>
              <div className="col-md-6 form-group">
                <label htmlFor="hash">Hash</label>
                <input id="hash" type="text" className="form-control" />
              </div>
              <div className="col-md-6 form-group">
                <label htmlFor="signal-type">Signal Type</label>
                <select id="signal-type" className="form-control">
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
            <div className="text-right mb-4">
              <button type="button" className="btn btn-secondary">
                Clear
              </button>
              <button type="button" className="btn btn-primary ml-2">
                Apply
              </button>
            </div>
          </form>
        </div>
      </Collapse>
      <MatchList />
      <MatchDetailsModal show={showModal} onHide={() => setShowModal(false)} />
    </>
  );
}

function MatchList() {
  const [matchesData, setMatchesData] = useState(null);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    fetchMatches().then(matches => setMatchesData(matches.matches));
    // .catch(err => console.log(err));
  }, []);

  function formatTimestamp(timestamp) {
    return new Intl.DateTimeFormat('defualt', {
      day: 'numeric',
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }).format(new Date(timestamp));
  }

  return (
    <>
      <Spinner hidden={matchesData !== null} animation="border" role="status">
        <span className="sr-only">Loading...</span>
      </Spinner>
      <Collapse in={matchesData !== null}>
        <div className="row mt-3">
          <div className="col-xs-12">
            <table className="table table-hover table-sm">
              <thead>
                <tr>
                  <th>Content</th>
                  <th>Matched Signal ID</th>
                  <th>Source</th>
                  <th>Last Updated</th>
                  <th>Reaction</th>
                  <th>
                    {/* for now have this at the header button so we still have an example of a model  */}
                    <button
                      type="button"
                      className="btn btn-outline-primary btn-sm"
                      onClick={() => setShowModal(true)}>
                      Details
                    </button>
                  </th>
                </tr>
              </thead>
              <tbody>
                {matchesData !== null && matchesData.length ? (
                  matchesData.map(match => (
                    <tr className="align-middle" key={match.content_id}>
                      <td className="align-middle">{match.content_id}</td>
                      <td className="align-middle">{match.signal_id}</td>
                      <td className="align-middle">{match.signal_source}</td>
                      <td className="align-middle">
                        {formatTimestamp(match.updated_at)}
                      </td>
                      <td className="align-middle">{match.reactions}</td>
                      <td className="align-middle">
                        <Link
                          to="/matches/file1.jpg"
                          className="btn btn-outline-primary btn-sm">
                          Details
                        </Link>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5}>No Matches Found.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </Collapse>
      <MatchDetailsModal show={showModal} onHide={() => setShowModal(false)} />
    </>
  );
}

function MatchDetailsModal(props) {
  // TODO add prop typing
  // eslint-disable-next-line react/prop-types
  const {show, onHide} = props;
  return (
    <Modal
      show={show}
      onHide={onHide}
      size="lg"
      aria-labelledby="contained-modal-title-vcenter"
      centered>
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
        <Button onClick={onHide}>Close</Button>
      </Modal.Footer>
    </Modal>
  );
}
