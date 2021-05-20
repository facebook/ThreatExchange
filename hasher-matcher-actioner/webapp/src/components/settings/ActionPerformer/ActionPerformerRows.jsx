/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState} from 'react';
import {PropTypes} from 'prop-types';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import ActionPerformerColumns from './ActionPerformerColumns';

export default function ActionPerformerRows({
  name,
  type,
  params,
  edit,
  onSave,
  onDelete,
}) {
  const [editing, setEditing] = useState(edit);
  const [
    showDeleteActionRuleConfirmation,
    setShowDeleteActionRuleConfirmation,
  ] = useState(false);
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
          </Button>{' '}
          <Button
            variant="secondary"
            className="table-action-button"
            onClick={() => setShowDeleteActionRuleConfirmation(true)}>
            <ion-icon
              name="trash-bin"
              size="large"
              className="ion-icon-white"
            />
          </Button>
          <Modal
            show={showDeleteActionRuleConfirmation}
            onHide={() => setShowDeleteActionRuleConfirmation(false)}>
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
                onClick={() => setShowDeleteActionRuleConfirmation(false)}>
                Cancel
              </Button>
              <Button variant="primary" onClick={() => onDelete(name)}>
                Yes, Delete This Action
              </Button>
            </Modal.Footer>
          </Modal>
        </td>
        <ActionPerformerColumns
          key={updatedAction.name}
          name={updatedAction.name}
          type={updatedAction.config_subtype}
          params={updatedAction.fields}
          editing={false}
          create={false}
          onChange={onUpdatedActionChange}
        />
      </tr>
      <tr hidden={!editing}>
        <td>
          <Button
            variant="outline-primary"
            className="mb-2 table-action-button"
            onClick={() => {
              onSave(updatedAction);
              setEditing(false);
            }}>
            <ion-icon
              name="checkmark"
              size="large"
              className="ion-icon-white"
            />
          </Button>{' '}
          <Button
            variant="outline-secondary"
            className="table-action-button"
            onClick={() => {
              resetForm();
              setEditing(false);
            }}>
            <ion-icon name="close" size="large" className="ion-icon-white" />
          </Button>
        </td>
        <ActionPerformerColumns
          name={updatedAction.name}
          type={updatedAction.config_subtype}
          params={updatedAction.fields}
          editing
          create={false}
          onChange={onUpdatedActionChange}
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
};
