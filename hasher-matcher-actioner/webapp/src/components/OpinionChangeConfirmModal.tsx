/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React, {useState} from 'react';
import {Button, Col, Row, Modal, Container} from 'react-bootstrap';

import {PENDING_OPINION_CHANGE} from '../utils/constants';
import {requestSignalOpinionChange} from '../Api';

type OpinionChangeConfirmModalProps = {
  show?: boolean;
  onHide: () => void;
  onSubmit: () => void;
  privacyGroupId: string;
  signalId: string;
  signalSource: string;
  opinion?: string; // TODO enum
  pendingOpinionChange?: string; // TODO enum
};

export default function OpinionChangeConfirmModal({
  show,
  onHide,
  onSubmit,
  privacyGroupId,
  signalId,
  signalSource,
  opinion,
  pendingOpinionChange,
}: OpinionChangeConfirmModalProps): JSX.Element {
  const [submitting, setSubmitting] = useState(false);

  let changeText = '';
  switch (pendingOpinionChange) {
    case PENDING_OPINION_CHANGE.MARK_TRUE_POSITIVE:
      changeText = 'Mark this signal as a true positive?';
      break;
    case PENDING_OPINION_CHANGE.MARK_FALSE_POSITIVE:
      changeText = 'Mark this signal as a false positive?';
      break;
    case PENDING_OPINION_CHANGE.REMOVE_OPINION:
      changeText = 'Remove your opinion on this signal?';
      break;
    default:
      changeText = 'No change currently available.';
      break;
  }

  return (
    <Modal
      show={show}
      onHide={onHide}
      size="lg"
      aria-labelledby="contained-modal-title-vcenter"
      centered>
      <Modal.Header closeButton>
        <Modal.Title id="contained-modal-title-vcenter">
          Update Opinion?
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Container>
          <Row className="mb-2">
            Signal ID: {`(${signalSource}) ${signalId} `}
          </Row>
          <Row className="mb-2">PrivacyGroup ID: {privacyGroupId}</Row>
          <Row as="strong" className="mb-2">
            Current Opinion: {opinion}
          </Row>
          <Row className="mb-2">{changeText}</Row>
        </Container>
      </Modal.Body>
      <Modal.Footer>
        <Col id="align-left">
          Hitting confirm will send the update to the signal provider{' '}
          {signalSource === 'te' ? '(ThreatExchange)' : ''}
        </Col>
        <Button variant="secondary" onClick={onHide}>
          Close
        </Button>
        <Button
          onClick={() => {
            setSubmitting(true);
            requestSignalOpinionChange(
              signalId,
              signalSource,
              privacyGroupId,
              pendingOpinionChange as string,
            ).then(() => {
              setSubmitting(false);
              onSubmit();
              onHide();
            });
          }}>
          {submitting ? 'Submitting...' : 'Confirm'}
        </Button>
      </Modal.Footer>
    </Modal>
  );
}

OpinionChangeConfirmModal.defaultProps = {
  show: false,
  opinion: undefined,
  pendingOpinionChange: PENDING_OPINION_CHANGE.NONE,
};
