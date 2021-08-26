/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState} from 'react';
import {PropTypes} from 'prop-types';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import Tooltip from 'react-bootstrap/Tooltip';
import ActionPerformerColumns from './ActionPerformerColumns';

export default function ActionPerformerRows({
  name,
  type,
  params,
  edit,
  onSave,
  onDelete,
  canNotDeleteOrUpdateName,
}) {
  const [editing, setEditing] = useState(edit);
  const [showDeleteActionConfirmation, setShowDeleteActionConfirmation] =
    useState(false);
  const [showUpdateActionConfirmation, setShowUpdateActionConfirmation] =
    useState(false);
  const [updatedAction, setUpdatedAction] = useState({
    name,
    config_subtype: type,
    fields: params,
  });

  const onUpdatedActionChange = (key, value) => {
    if (key === 'name' || key === 'config_subtype') {
      setUpdatedAction({...updatedAction, ...value});
    } else {
      setUpdatedAction({
        ...updatedAction,
        fields: {...updatedAction.fields, ...value},
      });
    }
  };

  const resetForm = () => {
    setUpdatedAction({
      name,
      config_subtype: type,
      fields: params,
    });
  };

  return (
    <>
      <tr hidden={editing}>
        <td>
          <Button
            className="mb-2 table-action-button"
            onClick={() => setEditing(true)}>
            <ion-icon name="pencil" size="large" className="ion-icon-white" />
          </Button>
          <br />
          <Button
            variant="secondary"
            className="table-action-button"
            disabled={canNotDeleteOrUpdateName}
            onClick={() => setShowDeleteActionConfirmation(true)}>
            <ion-icon
              name="trash-bin"
              size="large"
              className="ion-icon-white"
            />
          </Button>
          <br />
          <Modal
            show={showDeleteActionConfirmation}
            onHide={() => setShowDeleteActionConfirmation(false)}>
            <Modal.Header closeButton>
              <Modal.Title>Confirm Action Delete</Modal.Title>
            </Modal.Header>
            <Modal.Body>
              <p>
                Please confirm you want to delete the action named{' '}
                <strong>{name}</strong>.
              </p>
            </Modal.Body>
            <Modal.Footer>
              <Button
                variant="secondary"
                onClick={() => setShowDeleteActionConfirmation(false)}>
                Cancel
              </Button>
              <Button variant="primary" onClick={() => onDelete(name)}>
                Yes, Delete This Action
              </Button>
            </Modal.Footer>
          </Modal>
          {canNotDeleteOrUpdateName ? (
            <OverlayTrigger
              overlay={
                <Tooltip id={`tooltip-${name}`}>
                  The action {name} can not be deleted because it is currently
                  being used by one or more action rules. Please edit the
                  rule(s) to refer to another action, or delete the rule(s),
                  then retry.
                </Tooltip>
              }>
              <Button variant="secondary" className="table-action-button">
                <ion-icon
                  name="help-outline"
                  size="large"
                  className="ion-icon-white"
                />
              </Button>
            </OverlayTrigger>
          ) : null}
        </td>
        <ActionPerformerColumns
          key={updatedAction.name}
          name={updatedAction.name}
          type={updatedAction.config_subtype}
          params={updatedAction.fields}
          editing={false}
          onChange={onUpdatedActionChange}
          canNotDeleteOrUpdateName={canNotDeleteOrUpdateName}
        />
      </tr>
      <tr hidden={!editing}>
        <td>
          <Button
            variant="outline-primary"
            className="mb-2 table-action-button"
            onClick={() => {
              setShowUpdateActionConfirmation(true);
            }}>
            <ion-icon
              name="checkmark"
              size="large"
              className="ion-icon-white"
            />
          </Button>
          <br />
          <Button
            variant="outline-secondary"
            className="table-action-button"
            onClick={() => {
              resetForm();
              setEditing(false);
            }}>
            <ion-icon name="close" size="large" className="ion-icon-white" />
          </Button>
          <Modal
            show={showUpdateActionConfirmation}
            onHide={() => setShowUpdateActionConfirmation(false)}>
            <Modal.Header closeButton>
              <Modal.Title>Confirm Action Update</Modal.Title>
            </Modal.Header>
            <Modal.Body>
              <p>
                Please confirm you want to update the action named{' '}
                <strong>{name}</strong>.
              </p>
            </Modal.Body>
            <Modal.Footer>
              <Button
                variant="secondary"
                onClick={() => setShowUpdateActionConfirmation(false)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={() => {
                  setEditing(false);
                  onSave({name, type, updatedAction});
                  setShowUpdateActionConfirmation(false);
                }}>
                Yes, Update This Action
              </Button>
            </Modal.Footer>
          </Modal>
        </td>
        <ActionPerformerColumns
          name={updatedAction.name}
          type={updatedAction.config_subtype}
          params={updatedAction.fields}
          editing
          onChange={onUpdatedActionChange}
          canNotDeleteOrUpdateName={canNotDeleteOrUpdateName}
        />
      </tr>
    </>
  );
}

ActionPerformerRows.propTypes = {
  name: PropTypes.string.isRequired,
  type: PropTypes.string.isRequired,
  edit: PropTypes.bool.isRequired,
  params: PropTypes.shape({
    url: PropTypes.string.isRequired,
    headers: PropTypes.string.isRequired,
  }).isRequired,
  onSave: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  canNotDeleteOrUpdateName: PropTypes.bool.isRequired,
};
