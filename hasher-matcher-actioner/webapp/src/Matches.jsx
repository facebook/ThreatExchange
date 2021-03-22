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
      <div className="row mt-3">
        <div className="col-xs-12">
          <table className="table table-hover table-sm">
            <thead>
              <tr>
                <th>Image</th>
                <th>Hash</th>
                <th>Matched On</th>
                <th>Reaction</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              <tr className="align-middle">
                <td className="align-middle">file1.jpg</td>
                <td className="align-middle">
                  8a551807446ba95400eb032ba8fe51c3857eaaa5570cea70bb87775cbdc1eebe
                </td>
                <td className="align-middle">5 Feb 2021 1:47pm</td>
                <td className="align-middle">Seen</td>
                <td className="align-middle">
                  <button
                    type="button"
                    className="btn btn-outline-primary btn-sm"
                    onClick={() => setShowModal(true)}>
                    Details
                  </button>
                </td>
              </tr>
              <tr>
                <td className="align-middle">file1.jpg</td>
                <td className="align-middle">
                  652fe95ab4ae5129c07e92da787e525ab44b736ea5ab5ce4485ba344158b8e86
                </td>
                <td className="align-middle">5 Feb 2021 1:44pm</td>
                <td className="align-middle">Seen</td>
                <td className="align-middle">
                  <Link
                    to="/matches/file1.jpg"
                    className="btn btn-outline-primary btn-sm">
                    Details
                  </Link>
                </td>
              </tr>
              <tr>
                <td className="align-middle">file2.jpg</td>
                <td className="align-middle">
                  652fe95ab4ae5129c07e92da787e525ab44b736ea5ab5ce4485ba344158b8e86
                </td>
                <td className="align-middle">5 Feb 2021 1:44pm</td>
                <td className="align-middle">Positive</td>
                <td className="align-middle">
                  <button
                    type="button"
                    className="btn btn-outline-primary btn-sm">
                    Details
                  </button>
                </td>
              </tr>
              <tr>
                <td className="align-middle">file3.jpg</td>
                <td className="align-middle">
                  652fe95ab4ae5129c07e92da787e525ab44b736ea5ab5ce4485ba344158b8e86
                </td>
                <td className="align-middle">5 Feb 2021 1:44pm</td>
                <td className="align-middle">Positive</td>
                <td className="align-middle">
                  <button
                    type="button"
                    className="btn btn-outline-primary btn-sm">
                    Details
                  </button>
                </td>
              </tr>
              <tr>
                <td className="align-middle">file4.jpg</td>
                <td className="align-middle">
                  652fe95ab4ae5129c07e92da787e525ab44b736ea5ab5ce4485ba344158b8e86
                </td>
                <td className="align-middle">5 Feb 2021 1:44pm</td>
                <td className="align-middle">False Positive</td>
                <td className="align-middle">
                  <button
                    type="button"
                    className="btn btn-outline-primary btn-sm">
                    Details
                  </button>
                </td>
              </tr>
              <tr>
                <td className="align-middle">file5.jpg</td>
                <td className="align-middle">
                  652fe95ab4ae5129c07e92da787e525ab44b736ea5ab5ce4485ba344158b8e86
                </td>
                <td className="align-middle">5 Feb 2021 1:44pm</td>
                <td className="align-middle">Seen</td>
                <td className="align-middle">
                  <button
                    type="button"
                    className="btn btn-outline-primary btn-sm">
                    Details
                  </button>
                </td>
              </tr>
              <tr>
                <td className="align-middle">file6.jpg</td>
                <td className="align-middle">
                  652fe95ab4ae5129c07e92da787e525ab44b736ea5ab5ce4485ba344158b8e86
                </td>
                <td className="align-middle">5 Feb 2021 1:44pm</td>
                <td className="align-middle">Positive</td>
                <td className="align-middle">
                  <button
                    type="button"
                    className="btn btn-outline-primary btn-sm">
                    Details
                  </button>
                </td>
              </tr>
              <tr>
                <td className="align-middle">file7.jpg</td>
                <td className="align-middle">
                  652fe95ab4ae5129c07e92da787e525ab44b736ea5ab5ce4485ba344158b8e86
                </td>
                <td className="align-middle">5 Feb 2021 1:44pm</td>
                <td className="align-middle">Seen</td>
                <td className="align-middle">
                  <button
                    type="button"
                    className="btn btn-outline-primary btn-sm">
                    Details
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <MatchList2 />
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

function MatchList2() {
  const [matchesData, setMatchesData] = useState(null);

  useEffect(() => {
    fetchMatches().then(matches => setMatchesData(matches.matches));
    // .catch(err => console.log(err));
  }, []);

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
                  <th>Image</th>
                  <th>Hash</th>
                  <th>Matched On</th>
                  <th>Reaction</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {matchesData !== null && matchesData.length ? (
                  matchesData.map(match => {
                    const imgKey = Object.keys(match)[0];
                    const teVal = match[imgKey];
                    return (
                      <tr className="align-middle" key={imgKey}>
                        <td className="align-middle">{imgKey}</td>
                        <td className="align-middle">{teVal}</td>
                        <td className="align-middle">TODO</td>
                        <td className="align-middle">TODO</td>
                        <td className="align-middle">
                          <Link
                            to="/matches/file1.jpg"
                            className="btn btn-outline-primary btn-sm">
                            Details
                          </Link>
                        </td>
                      </tr>
                    );
                  })
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
    </>
  );
}
