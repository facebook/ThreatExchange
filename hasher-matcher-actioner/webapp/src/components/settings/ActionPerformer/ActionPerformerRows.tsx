/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import {IonIcon} from '@ionic/react';
import {checkmark, trashBin, pencil, helpOutline, close} from 'ionicons/icons';
import React, {useState} from 'react';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import Tooltip from 'react-bootstrap/Tooltip';
import ActionPerformerColumns from './ActionPerformerColumns';

type Params = {
  url: string;
  headers: string;
};

type Action = {
  name: string;
  type: string;
  updatedAction: any;
};

type ActionPerformerRowsProps = {
  name: string;
  type: string;
  params: Params;
  edit: boolean;
  onSave: (key: Action) => void;
  onDelete: (key: string) => void;
  canNotDeleteOrUpdateName: boolean;
};

export default function ActionPerformerRows({
  name,
  type,
  params,
  edit,
  onSave,
  onDelete,
  canNotDeleteOrUpdateName,
}: ActionPerformerRowsProps): JSX.Element {
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

  const onUpdatedActionChange = (
    key: string,
    value: {[key: string]: string},
  ) => {
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
            <IonIcon icon={pencil} size="large" />
          </Button>
          <br />
          <Button
            variant="secondary"
            className="table-action-button"
            disabled={canNotDeleteOrUpdateName}
            onClick={() => setShowDeleteActionConfirmation(true)}>
            <IonIcon icon={trashBin} size="large" color="white" />
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
                <IonIcon icon={helpOutline} size="large" color="white" />
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
            <IonIcon icon={checkmark} size="large" color="white" />
          </Button>
          <br />
          <Button
            variant="outline-secondary"
            className="table-action-button"
            onClick={() => {
              resetForm();
              setEditing(false);
            }}>
            <IonIcon icon={close} size="large" />
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
