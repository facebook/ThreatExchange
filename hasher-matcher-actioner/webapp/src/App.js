/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, { useState } from 'react';
import { BrowserRouter as Router, Route, Link, useHistory, useParams } from 'react-router-dom';
import { AnimatedSwitch } from 'react-router-transition';
import { Button, Col, Collapse, Form, Image, Modal, Row } from 'react-bootstrap'
import Spinner from 'react-bootstrap/Spinner'

export default function App() {
  return (
    <Router>
      <nav class="navbar navbar-expand-md navbar-dark bg-dark">
        <a class="navbar-brand" href="/">Hasher-Matcher-Actioner (HMA)</a>
        <ul class="navbar-nav mr-auto">
          <li class="nav-item">
            <Link to="/" className="nav-link">Dashboard</Link>
          </li>
          <li class="nav-item">
            <Link to="/matches" className="nav-link">Matches</Link>
          </li>
          <li class="nav-item">
            <Link to="/signals" className="nav-link">Signals</Link>
          </li>
          <li class="nav-item">
            <Link to="/upload" className="nav-link">Upload</Link>
          </li>
        </ul>
        <ul class="navbar-nav">
          <li class="nav-item">
            <Link to="/settings" className="nav-link"><span class="glyphicon glyphicon-cog"></span>Settings</Link>
          </li>
        </ul>
      </nav>
      <main role="main" class="container mt-4">
        <AnimatedSwitch
          atEnter={{ opacity: 0 }}
          atLeave={{ opacity: 0 }}
          atActive={{ opacity: 1 }}
          className="switch-wrapper"
          >
          <Route path="/matches/:id">
            <MatchDetails />
          </Route>
          <Route path="/matches">
            <Matches />
          </Route>
          <Route path="/signals">
            <Signals />
          </Route>
          <Route path="/upload">
            <Upload />
          </Route>
          <Route path="/settings">
            <Settings />
          </Route>
          <Route path="/">
            <Dashboard />
          </Route>
        </AnimatedSwitch>
      </main>
    </Router>
  );
}

function Dashboard() {
  const [showDrawer, setShowDrawer] = useState(false);
  const history = useHistory();
  return (
    <>
      <h1>Dashboard</h1>
      <div class="row mt-3">
        <div class="col-xl-4 col-lg-4 col-md-6 col-sm-6 col-xs-12 mb-4">
          <div class="card text-center">
            <div class="card-header text-white bg-success"><h4 class="mb-0">Hashes</h4></div>
            <div class="card-body"><h5>34,217,123,456</h5><h6>145,609,278 today</h6></div>
            <div class="card-footer"><small class="font-weight-light">as of 12 Mar 2021 2:03pm</small></div>
          </div>
        </div>
        <div class="col-xl-4 col-lg-4 col-md-6 col-sm-6 col-xs-12 mb-4">
          <div class="card text-center" onClick={() => history.push("/matches")} style={{cursor: "pointer"}}>
            <div class="card-header text-white bg-success"><h4 class="mb-0">Matches</h4></div>
            <div class="card-body"><h5>14,376</h5><h6>109 today</h6></div>
            <div class="card-footer"><small class="font-weight-light">last match 12 Mar 2021 11:03am</small></div>
          </div>
        </div>
        <div class="col-xl-4 col-lg-4 col-md-6 col-sm-6 col-xs-12 mb-4">
          <div class="card text-center">
            <div class="card-header text-white bg-success"><h4 class="mb-0">Actions</h4></div>
            <div class="card-body"><h5>3,456</h5><h6>27 today</h6></div>
            <div class="card-footer"><small class="font-weight-light">as of 12 Mar 2021 2:03pm</small></div>
          </div>
        </div>
        <div class="col-xl-4 col-lg-4 col-md-6 col-sm-6 col-xs-12 mb-4">
          <div class="card text-center" onClick={() => history.push("/signals")} style={{cursor: "pointer"}}>
            <div class="card-header text-white bg-success"><h4 class="mb-0">Signals</h4></div>
            <div class="card-body"><h5>123,456</h5><h6>654 today</h6></div>
            <div class="card-footer"><small class="font-weight-light">as of 12 Mar 2021 2:03pm</small></div>
          </div>
        </div>
        <div class="col-xl-4 col-lg-4 col-md-6 col-sm-6 col-xs-12 mb-4">
          <div class="card text-center">
            <div class="card-header text-white bg-success"><h4 class="mb-0">System Status</h4></div>
            <div class="card-body"><h5>Running</h5><h6>47 days</h6></div>
            <div class="card-footer"><small class="font-weight-light">running since 7 Feb 2021</small></div>
          </div>
        </div>
      </div>
    </>
  );
}

function Matches() {
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

function MatchDetails() {
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
              </tr>
            </tbody>
          </table>
        </Col>
      </Row>
    </>
  );
}

function Signals() {
  return (
    <>
      <h1>Signals</h1>
      <div class="row mt-3">
        <div class="col-md-12">
          <div class="card">
            <div class="card-header text-white bg-success"><h4 class="mb-0">Signal Source 1</h4></div>
            <div class="card-body">
              <table class="table mb-0">
                <thead>
                  <tr>
                    <th>Signal Type</th>
                    <th>Number of Signals</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>HASH_PDQ</td>
                    <td>12,456</td>
                  </tr>
                  <tr>
                    <td>HASH_PDQ_OCR</td>
                    <td>2,456</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="card-footer"><small class="font-weight-light">as of 12 Mar 2021 2:03pm</small></div>
          </div>
        </div>
        <div class="col-md-12 mt-4">
          <div class="card">
            <div class="card-header text-white bg-success"><h4 class="mb-0">Signal Source 2</h4></div>
            <div class="card-body">
              <table class="table mb-0">
                <thead>
                  <tr>
                    <th>Signal Type</th>
                    <th>Number of Signals</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>DEBUG_STRING</td>
                    <td>84,823</td>
                  </tr>
                  <tr>
                    <td>HASH_PDQ</td>
                    <td>587</td>
                  </tr>
                  <tr>
                    <td>HASH_PDQ_OCR</td>
                    <td>112</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="card-footer"><small class="font-weight-light">as of 12 Mar 2021 2:03pm</small></div>
          </div>
        </div>
      </div>
    </>
  );
}

function Upload() {
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

function Settings() {
  return (
    <>
      <h1>Settings</h1>
    </>
  );
}
