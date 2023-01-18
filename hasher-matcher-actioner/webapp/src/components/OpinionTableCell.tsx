/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React, {useState} from 'react';
import {Dropdown, DropdownButton, ButtonGroup} from 'react-bootstrap';
import {OPINION_STRING, PENDING_OPINION_CHANGE} from '../utils/constants';

import OpinionChangeConfirmModal from './OpinionChangeConfirmModal';

type OpinionChangeConfirmModalProps = {
  privacyGroupId: string;
  signalId: string;
  signalSource: string;
  opinion?: string;
  pendingOpinionChange?: string;
  setShowToast: (x: boolean) => void;
};

export default function OpinionTableCell({
  privacyGroupId,
  signalId,
  signalSource,
  opinion,
  pendingOpinionChange,
  setShowToast,
}: OpinionChangeConfirmModalProps): JSX.Element {
  const [newPendingOpinionChange, setNewPendingOpinionChange] = useState(
    PENDING_OPINION_CHANGE.NONE,
  );
  const [showModal, setShowModal] = useState(false);
  const [updatePending, setUpdatePending] = useState(
    pendingOpinionChange !== PENDING_OPINION_CHANGE.NONE,
  );
  return (
    <>
      <DropdownButton
        as={ButtonGroup}
        size="sm"
        id="dropdown-button-drop-down"
        className="ml-2 mb-6"
        title={updatePending ? `*${opinion}` : opinion}
        drop="right"
        variant={updatePending ? 'secondary' : 'primary'}
        style={{
          minWidth: '150px',
        }}>
        <Dropdown.Header>
          {updatePending ? 'Update is Pending.' : 'Update Opinion?'}
        </Dropdown.Header>

        {/* TODO these Dropdown.Item's logic is likely possible to generalize into a signal component */}
        <Dropdown.Item
          size="sm"
          disabled={
            opinion === OPINION_STRING.FALSE_POSITIVE ||
            opinion === OPINION_STRING.TRUE_POSITIVE ||
            (updatePending &&
              pendingOpinionChange !==
                PENDING_OPINION_CHANGE.MARK_FALSE_POSITIVE)
          }
          active={
            updatePending &&
            pendingOpinionChange === PENDING_OPINION_CHANGE.MARK_FALSE_POSITIVE
          }
          onClick={() => {
            if (!updatePending) {
              setNewPendingOpinionChange(
                PENDING_OPINION_CHANGE.MARK_FALSE_POSITIVE,
              );
              setShowModal(true);
            }
          }}>
          Mark False Positive
        </Dropdown.Item>
        <Dropdown.Item
          size="sm"
          disabled={
            opinion === OPINION_STRING.FALSE_POSITIVE ||
            opinion === OPINION_STRING.TRUE_POSITIVE ||
            (updatePending &&
              pendingOpinionChange !==
                PENDING_OPINION_CHANGE.MARK_TRUE_POSITIVE)
          }
          active={
            updatePending &&
            pendingOpinionChange === PENDING_OPINION_CHANGE.MARK_TRUE_POSITIVE
          }
          onClick={() => {
            if (!updatePending) {
              setNewPendingOpinionChange(
                PENDING_OPINION_CHANGE.MARK_TRUE_POSITIVE,
              );
              setShowModal(true);
            }
          }}>
          Mark True Positive
        </Dropdown.Item>
        <Dropdown.Item
          size="sm"
          disabled={
            OPINION_STRING.UKNOWN === opinion ||
            OPINION_STRING.DISPUTED === opinion ||
            (updatePending &&
              pendingOpinionChange !== PENDING_OPINION_CHANGE.REMOVE_OPINION)
          }
          active={
            updatePending &&
            pendingOpinionChange === PENDING_OPINION_CHANGE.REMOVE_OPINION
          }
          onClick={() => {
            if (!updatePending) {
              setNewPendingOpinionChange(PENDING_OPINION_CHANGE.REMOVE_OPINION);
              setShowModal(true);
            }
          }}>
          Remove My Opinion
        </Dropdown.Item>
      </DropdownButton>
      <OpinionChangeConfirmModal
        show={showModal}
        onHide={() => setShowModal(false)}
        onSubmit={() => {
          setShowToast(true);
          setUpdatePending(true);
        }}
        privacyGroupId={privacyGroupId}
        signalId={signalId}
        signalSource={signalSource}
        opinion={opinion}
        pendingOpinionChange={newPendingOpinionChange}
      />
    </>
  );
}

OpinionTableCell.defaultProps = {
  opinion: OPINION_STRING.UKNOWN,
  pendingOpinionChange: PENDING_OPINION_CHANGE.NONE,
};
