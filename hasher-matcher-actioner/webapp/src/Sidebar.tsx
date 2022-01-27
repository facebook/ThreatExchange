/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState} from 'react';
import {Modal, Container, Row, Col, Button} from 'react-bootstrap';
import {NavLink} from 'react-router-dom';
import {Auth} from 'aws-amplify';
import './styles/_sidebar.scss';

type SidebarProps = {
  className: string;
};

export default function Sidebar(
  {className}: SidebarProps = {className: 'sidebar'},
): JSX.Element {
  const [showLogoutModal, setShowLogoutModal] = useState(false);

  return (
    <div className={`${className} d-flex flex-column`}>
      <div className="px-2 pt-2 pb-4Right">
        <a className="navbar-brand alert-link" href="/">
          HMA
        </a>
      </div>
      <ul className="navbar-nav mb-auto">
        {/* <li className="nav-item">
          <NavLink
            exact
            activeClassName="text-white bg-secondary rounded"
            to="/"
            className="nav-link px-2">
            Dashboard
          </NavLink>
        </li> */}
        <li className="nav-item">
          <NavLink
            activeClassName="text-white bg-secondary rounded"
            to="/matches"
            className="nav-link px-2">
            Matches
          </NavLink>
        </li>
        <li className="nav-item">
          <NavLink
            activeClassName="text-white bg-secondary rounded"
            to="/submit"
            className="nav-link px-2">
            Submit Content
          </NavLink>
        </li>
        <li className="nav-item">
          <NavLink
            activeClassName="text-white bg-secondary rounded"
            to="/banks/"
            className="nav-link px-2">
            Banks
          </NavLink>
        </li>
      </ul>

      <ul className="navbar-nav push-down pb-2 pt-1">
        <li className="nav-item">
          <NavLink
            activeClassName="text-white bg-secondary rounded"
            to="/settings"
            className="nav-link px-2">
            Settings
          </NavLink>
        </li>
        <li className="nav-item">
          <Button
            variant="link"
            className="nav-link px-1"
            onClick={() => setShowLogoutModal(true)}>
            Sign Out
          </Button>
        </li>
      </ul>
      <Modal show={showLogoutModal} size="lg" centered>
        <Modal.Header closeButton onHide={() => setShowLogoutModal(false)}>
          <Modal.Title>Logout</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Container>
            <Row>
              <Col>
                <p>Are you sure you want to sign out?</p>
                <Button
                  variant="primary"
                  onClick={() => Auth.signOut()}
                  href="/">
                  Yes. Sign me out.
                </Button>
              </Col>
            </Row>
          </Container>
        </Modal.Body>
      </Modal>
    </div>
  );
}
