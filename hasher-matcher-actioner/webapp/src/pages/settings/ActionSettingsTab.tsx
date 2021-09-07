/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState} from 'react';
import Card from 'react-bootstrap/Card';
import Table from 'react-bootstrap/Table';
import Button from 'react-bootstrap/Button';
import Toast from 'react-bootstrap/Toast';
import {IonIcon} from '@ionic/react';
import {add, checkmark, close} from 'ionicons/icons';
import {updateAction, createAction, deleteAction} from '../../Api';
import ActionPerformerColumns, {
  WebhookActionPerformerParams,
} from '../../components/settings/ActionPerformer/ActionPerformerColumns';
import ActionPerformerRows from '../../components/settings/ActionPerformer/ActionPerformerRows';
import {ActionRule} from './ActionRuleSettingsTab';

type Input = {
  actions: Action[];
  setActions: (actions: Action[]) => void;
  actionRules: ActionRule[];
};

export class Action {
  name: string;

  config_subtype: string;

  params: WebhookActionPerformerParams;

  constructor(
    name: string,
    config_subtype: string,
    url: string,
    headers: string,
  ) {
    this.name = name;
    this.config_subtype = config_subtype;
    this.params = {url, headers};
  }
}

const defaultAction = new Action('', '', '', '');

/**
 * TODO This used to have an ActionLabel Settings component here. The
 * action rules are now in a separate tab. We can now rename this
 * outer component to ActionPerformerSettingsTab and start the
 * implementation of that component here. Not doing that now because
 * someone else is actively working in this space.
 */
export default function ActionSettingsTab({
  actions,
  setActions,
  actionRules,
}: Input): JSX.Element {
  const [adding, setAdding] = useState(false);
  const [newAction, setNewAction] = useState(defaultAction);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const resetForm = () => {
    setNewAction(defaultAction);
  };
  const displayToast = (message: string) => {
    setToastMessage(message);
    setShowToast(true);
  };
  const onActionUpdate = (
    old_name: string,
    old_type: string,
    updatedAction: Action,
  ) => {
    updateAction(old_name, old_type, updatedAction)
      .then(response => {
        const updatedActions = actions.map(action => {
          if (action.name === old_name) {
            return updatedAction;
          }
          return action;
        });
        setActions(updatedActions);
        displayToast(response.response);
      })
      .catch(e => {
        /* eslint-disable-next-line no-console */
        console.log(e);
        displayToast('Errors when updating the action. Please try again later');
      });
  };
  const onActionCreate = () => {
    createAction(newAction)
      .then(response => {
        displayToast(response.response);
        const newActions = actions;
        newActions.unshift(newAction);
        setActions(newActions);
        resetForm();
        setAdding(false);
      })
      .catch(() => {
        displayToast('Errors when creating the action. Please try again later');
      });
  };
  const onActionDelete = (actionToDelete: Action) => {
    deleteAction(actionToDelete.name)
      .then(response => {
        const filteredActions = actions.filter(
          (action: Action) => action.name !== actionToDelete.name,
        );
        setActions(filteredActions);
        displayToast(response.response);
      })
      .catch(() => {
        displayToast('Errors when deleting the action. Please try again later');
      });
  };

  return (
    <>
      <Card>
        <Card.Header>
          <h2 className="mt-2">Action Definitions</h2>
          <p className="mt-5">
            Actions are how HMA notifies another system (such as your platform)
            that a Match has occurred. For example, there is a Dataset of cat
            images and your platform does not allow cat images, after a piece of
            Content matches the Dataset, your Platform should be notified so
            that you can review the Content and, if it is truly a cat, remove it
            for violating your Platform&apos;s Community Standards.
          </p>
          <div className="feedback-toast-container">
            <Toast
              onClose={() => setShowToast(false)}
              show={showToast}
              delay={5000}
              autohide>
              <Toast.Body>{toastMessage}</Toast.Body>
            </Toast>
          </div>
        </Card.Header>
        <Card.Body>
          <Table striped bordered hover>
            <thead>
              <tr>
                <th>
                  <Button
                    className="table-action-button"
                    onClick={() => setAdding(true)}>
                    <IonIcon icon={add} size="large" />
                  </Button>
                </th>
                <th>Action Name</th>
                <th>Action Details</th>
              </tr>
            </thead>
            <tbody>
              <tr hidden={!adding}>
                <td>
                  <Button
                    variant="outline-primary"
                    className="mb-2 table-action-button"
                    onClick={() => {
                      onActionCreate();
                    }}>
                    <IonIcon icon={checkmark} size="large" color="white" />
                  </Button>{' '}
                  <Button
                    variant="outline-secondary"
                    className="table-action-button"
                    onClick={() => {
                      resetForm();
                      setAdding(false);
                    }}>
                    <IonIcon icon={close} size="large" color="white" />
                  </Button>
                </td>
                <ActionPerformerColumns
                  action={newAction}
                  editing
                  updateAction={setNewAction}
                  canNotDeleteOrUpdateName={false}
                />
              </tr>
              {actions.length === 0
                ? null
                : actions.map(action => (
                    <ActionPerformerRows
                      key={action.name}
                      action={action}
                      saveAction={updatedAction =>
                        onActionUpdate(
                          action.name,
                          action.config_subtype,
                          updatedAction,
                        )
                      }
                      deleteAction={onActionDelete}
                      canNotDeleteOrUpdateName={
                        // Check if any ActionRule is using this Action
                        actionRules.findIndex(
                          action_rule => action_rule.action === action.name,
                        ) >= 0
                      }
                    />
                  ))}
            </tbody>
          </Table>
        </Card.Body>
      </Card>
    </>
  );
}
