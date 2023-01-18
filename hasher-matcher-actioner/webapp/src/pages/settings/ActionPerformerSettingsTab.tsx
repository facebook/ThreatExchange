/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React, {useContext, useState} from 'react';
import Card from 'react-bootstrap/Card';
import Table from 'react-bootstrap/Table';
import Button from 'react-bootstrap/Button';
import {IonIcon} from '@ionic/react';
import {add, checkmark, close, notificationsOutline} from 'ionicons/icons';
import {updateAction, createAction, deleteAction} from '../../Api';
import ActionPerformerColumns from '../../components/settings/ActionPerformer/ActionPerformerColumns';
import ActionPerformerRows from '../../components/settings/ActionPerformer/ActionPerformerRows';
import {ActionRule} from './ActionRuleSettingsTab';
import {ActionPerformerType} from '../../utils/constants';
import {NotificationsContext} from '../../AppWithNotifications';

type Input = {
  actions: ActionPerformer[];
  setActions: (actions: ActionPerformer[]) => void;
  actionRules: ActionRule[];
};

export type ActionPerformerParams = {
  url?: string;
  headers?: string;
  extension_name?: string;
  additional_kwargs?: Record<string, string>;
};

export type ActionPerformer = {
  name: string;
  config_subtype: string;
  params: ActionPerformerParams;
};

const defaultAction: ActionPerformer = {
  name: '',
  config_subtype: '',
  params: {url: '', headers: '', extension_name: '', additional_kwargs: {}},
};

// Right now the API (or more specifically the config.py HMAConfig class)
// does not handle unexpected null fields cleanly therefore for now
// we define the set of expected params and filter out the others
// before sending creation or update requests.
const webhookParams = ['url', 'headers'];
const customParams = ['extension_name', 'additional_kwargs'];

const expectedParamsMap: Record<string, string[]> = {
  [ActionPerformerType.WebhookPostActionPerformer]: webhookParams,
  [ActionPerformerType.WebhookGetActionPerformer]: webhookParams,
  [ActionPerformerType.WebhookDeleteActionPerformer]: webhookParams,
  [ActionPerformerType.WebhookPutActionPerformer]: webhookParams,
  [ActionPerformerType.CustomImplActionPerformer]: customParams,
};

const removeUnexpectedParams = (action: ActionPerformer): ActionPerformer => {
  const expectedParams = expectedParamsMap[action.config_subtype];
  const newParams: Record<string, string | Record<string, string> | undefined> =
    {};
  expectedParams.forEach(param => {
    newParams[param] = action.params[param as keyof ActionPerformerParams];
  });
  const newAction = action;
  newAction.params = newParams;
  return newAction;
};

export default function ActionPerformerSettingsTab({
  actions,
  setActions,
  actionRules,
}: Input): JSX.Element {
  const [adding, setAdding] = useState(false);
  const [newAction, setNewAction] = useState(defaultAction);
  const notifications = useContext(NotificationsContext);

  const resetForm = () => {
    setNewAction(defaultAction);
  };
  const onActionUpdate = (
    old_name: string,
    old_type: string,
    updatedAction: ActionPerformer,
  ) => {
    updateAction(old_name, old_type, removeUnexpectedParams(updatedAction))
      .then(response => {
        const updatedActions = actions.map(action => {
          if (action.name === old_name) {
            return updatedAction;
          }
          return action;
        });
        setActions(updatedActions);
        notifications.success({
          message: `${response.response} (Manual refresh maybe necessary to see changes.)`,
        });
      })
      .catch(e => {
        notifications.error({
          message: `Errors when updating the action. Please try again later\n${e.message}`,
        });
      });
  };
  const onActionCreate = () => {
    createAction(removeUnexpectedParams(newAction))
      .then(response => {
        notifications.success({
          message: `${response.response} (Manual refresh maybe necessary to see changes.)`,
        });
        const newActions = actions;
        newActions.unshift(newAction);
        setActions(newActions);
        resetForm();
        setAdding(false);
      })
      .catch(e => {
        notifications.error({
          message: `Errors when creating the action. Please try again later\n${e.message}`,
        });
      });
  };
  const onActionDelete = (actionToDelete: ActionPerformer) => {
    deleteAction(actionToDelete.name)
      .then(response => {
        const filteredActions = actions.filter(
          (action: ActionPerformer) => action.name !== actionToDelete.name,
        );
        setActions(filteredActions);
        notifications.success({message: `${response.response}`});
      })
      .catch(e => {
        notifications.error({
          message: `Errors when deleting the action. Please try again later\n${e.message}`,
        });
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
                          action_rule =>
                            action_rule.action_name === action.name,
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
