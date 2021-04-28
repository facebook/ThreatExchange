/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState} from 'react';
import {Dropdown, DropdownButton, ButtonGroup} from 'react-bootstrap';
import PropTypes from 'prop-types';
import {OPINION_STRING, PENDING_OPINION_CHANGE} from '../utils/constants';

import OpinionChangeConfirmModal from './OpinionChangeConfirmModal';

export default function OpinionTableCell({
  dataset,
  signalId,
  signalSource,
  opinion,
  pendingOpinionChange,
  setShowToast,
}) {
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
            OPINION_STRING.FALSE_POSITIVE === opinion ||
            (updatePending &&
              pendingOpinionChange !==
                PENDING_OPINION_CHANGE.MARK_FALSE_POSITIVE)
          }
          active={
            updatePending &&
            pendingOpinionChange === PENDING_OPINION_CHANGE.MARK_FALSE_POSITIVE
          }
          onClick={
            updatePending
              ? () => {}
              : () => {
                  setNewPendingOpinionChange(
                    PENDING_OPINION_CHANGE.MARK_FALSE_POSITIVE,
                  );
                  setShowModal(true);
                }
          }>
          Mark False Positive
        </Dropdown.Item>
        <Dropdown.Item
          size="sm"
          disabled={
            OPINION_STRING.TRUE_POSITIVE === opinion ||
            (updatePending &&
              pendingOpinionChange !==
                PENDING_OPINION_CHANGE.MARK_TRUE_POSITIVE)
          }
          active={
            updatePending &&
            pendingOpinionChange === PENDING_OPINION_CHANGE.MARK_TRUE_POSITIVE
          }
          onClick={
            updatePending
              ? () => {}
              : () => {
                  setNewPendingOpinionChange(
                    PENDING_OPINION_CHANGE.MARK_TRUE_POSITIVE,
                  );
                  setShowModal(true);
                }
          }>
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
          onClick={
            updatePending
              ? () => {}
              : () => {
                  setNewPendingOpinionChange(
                    PENDING_OPINION_CHANGE.REMOVE_OPINION,
                  );
                  setShowModal(true);
                }
          }>
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
        dataset={dataset}
        signalId={signalId}
        signalSource={signalSource}
        opinion={opinion}
        pendingOpinionChange={newPendingOpinionChange}
      />
    </>
  );
}

OpinionTableCell.propTypes = {
  dataset: PropTypes.string,
  signalId: PropTypes.string,
  signalSource: PropTypes.string,
  opinion: OPINION_STRING,
  pendingOpinionChange: PENDING_OPINION_CHANGE,
  setShowToast: PropTypes.func,
};

OpinionTableCell.defaultProps = {
  dataset: undefined,
  signalId: undefined,
  signalSource: undefined,
  opinion: OPINION_STRING.UKNOWN,
  pendingOpinionChange: PENDING_OPINION_CHANGE.NONE,
  setShowToast: undefined,
};
