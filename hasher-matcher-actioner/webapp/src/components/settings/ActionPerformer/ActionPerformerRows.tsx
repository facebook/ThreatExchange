/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import {IonIcon} from '@ionic/react';
import {checkmark, trashBin, pencil, close} from 'ionicons/icons';
import React, {useContext, useState} from 'react';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import {ConfirmationsContext} from '../../../AppWithConfirmations';
import {ActionPerformer} from '../../../pages/settings/ActionPerformerSettingsTab';
import ActionPerformerColumns from './ActionPerformerColumns';

type ActionPerformerRowsProps = {
  action: ActionPerformer;
  saveAction: (newAction: ActionPerformer) => void;
  deleteAction: (oldAction: ActionPerformer) => void;
  canNotDeleteOrUpdateName: boolean;
};

export default function ActionPerformerRows({
  action,
  saveAction,
  deleteAction,
  canNotDeleteOrUpdateName,
}: ActionPerformerRowsProps): JSX.Element {
  const [editing, setEditing] = useState(false);
  const newAction = {...action};
  const [updatedAction, setUpdatedAction] = useState(newAction);

  const confirmations = useContext(ConfirmationsContext);
  const showDeleteActionConfirmation = () => {
    confirmations.confirm({
      message: `Please confirm you want to delete the action named "${action.name}"`,
      ctaText: 'Yes. Delete this Action.',
      ctaVariant: 'danger',
      onCancel: () => undefined,
      onConfirm: () => deleteAction(action),
    });
  };

  const showUpdateActionConfirmation = () => {
    confirmations.confirm({
      message: `Please confirm you want to update the action named ${action.name}`,
      ctaVariant: 'primary',
      ctaText: 'Yes. Update this Action.',
      onCancel: () => undefined,
      onConfirm: () => {
        setEditing(false);
        saveAction(updatedAction);
      },
    });
  };

  const resetForm = () => {
    setUpdatedAction(action);
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
            onClick={showDeleteActionConfirmation}>
            <IonIcon icon={trashBin} size="large" color="white" />
          </Button>
          <br />
        </td>
        <ActionPerformerColumns
          action={updatedAction}
          editing={false}
          updateAction={setUpdatedAction}
          canNotDeleteOrUpdateName={canNotDeleteOrUpdateName}
        />
      </tr>
      <tr hidden={!editing}>
        <td>
          <Button
            variant="outline-primary"
            className="mb-2 table-action-button"
            onClick={showUpdateActionConfirmation}>
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
        </td>
        <ActionPerformerColumns
          action={updatedAction}
          editing
          updateAction={setUpdatedAction}
          canNotDeleteOrUpdateName={canNotDeleteOrUpdateName}
        />
      </tr>
    </>
  );
}
