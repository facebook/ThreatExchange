/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';
import {Modal, Container, Row, Col, Form, Button} from 'react-bootstrap';
import {createBank} from '../../Api';
import BankDetailsForm from '../../forms/BankDetailsForm';

type AddBankModalProps = {
  show: boolean;
  onCloseClick: () => void;
};

/**
 * Even though this is a modal, it makes API calls and can be initialized on any
 * page. So DO NOT move this to components.
 */
export default function AddBankModal({show, onCloseClick}: AddBankModalProps) {
  return (
    <Modal show={show} size="lg" centered>
      <Modal.Header closeButton onHide={() => onCloseClick()}>
        <Modal.Title>Add Bank</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Container>
          <Row>
            <Col>
              <BankDetailsForm
                handleSubmit={(bankName, bankDescription) => {
                  createBank(bankName, bankDescription).then(() =>
                    onCloseClick(),
                  );
                }}
              />
            </Col>
          </Row>
        </Container>
      </Modal.Body>
    </Modal>
  );
}
