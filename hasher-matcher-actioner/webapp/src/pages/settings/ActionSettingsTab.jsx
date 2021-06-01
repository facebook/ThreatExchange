/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState, useEffect} from 'react';
import Card from 'react-bootstrap/Card';
import Table from 'react-bootstrap/Table';
import Button from 'react-bootstrap/Button';
import Toast from 'react-bootstrap/Toast';
import {
  fetchAllActions,
  updateAction,
  createAction,
  deleteAction,
  fetchAllActionRules,
} from '../../Api';
import ActionPerformerColumns from '../../components/settings/ActionPerformer/ActionPerformerColumns';
import ActionPerformerRows from '../../components/settings/ActionPerformer/ActionPerformerRows';

const defaultAction = {
  name: '',
  config_subtype: '',
  fields: {url: '', headers: ''},
};
export default function ActionSettingsTab() {
  /**
   * TODO This used to have an ActionLabel Settings component here. The
   * action rules are now in a separate tab. We can now rename this
   * outer component to ActionPerformerSettingsTab and start the
   * implementation of that component here. Not doing that now because
   * someone else is actively working in this space.
   */
  const [performers, setPerformers] = useState([]);
  const [
    actionRulesDependentActions,
    setActionRulesDependentActions,
  ] = useState([]);
  const [adding, setAdding] = useState(false);
  const [newAction, setNewAction] = useState(defaultAction);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const rename = ({name, config_subtype: type, ...rest}) => ({
    name,
    type,
    params: {...rest},
  });
  const resetForm = () => {
    setNewAction(defaultAction);
  };
  const onNewActionChange = (key, value) => {
    if (key === 'name' || key === 'config_subtype') {
      setNewAction({...newAction, ...value});
    } else {
      setNewAction({...newAction, fields: {...newAction.fields, ...value}});
    }
  };
  const displayToast = message => {
    setToastMessage(message);
    setShowToast(true);
  };
  const deleteActionUI = name => {
    const filteredPerformers = performers.filter(item => item.name !== name);
    setPerformers(filteredPerformers);
  };
  const refreshActions = () => {
    fetchAllActions().then(response => {
      const actionPerformers = response.actions_response.map(item =>
        rename(item),
      );
      setPerformers(actionPerformers);
    });
    fetchAllActionRules().then(response => {
      if (response && response.error_message === '') {
        const mappedActions = response.action_rules.map(
          actionRule => actionRule.action_label.value,
        );
        setActionRulesDependentActions(mappedActions);
      }
    });
  };
  const onActionUpdate = updatedAction => {
    updateAction(
      updatedAction.name,
      updatedAction.type,
      updatedAction.updatedAction,
    )
      .then(response => {
        displayToast(response.response);
        refreshActions();
      })
      .catch(() => {
        displayToast('Errors when updating the action. Please try again later');
      });
  };
  const onActionSave = () => {
    createAction(newAction)
      .then(response => {
        displayToast(response.response);
        refreshActions();
        resetForm();
        setAdding(false);
      })
      .catch(() => {
        displayToast('Errors when creating the action. Please try again later');
      });
  };
  const onActionDelete = name => {
    deleteAction(name)
      .then(response => {
        displayToast(response.response);
        deleteActionUI(name);
      })
      .catch(() => {
        displayToast('Errors when deleting the action. Please try again later');
      });
  };
  useEffect(() => {
    refreshActions();
  }, []);

  return (
    <>
      <Card>
        <Card.Header>
          <h2 className="mt-2">Action Definitions</h2>
          <h5 className="mt-5">Define what to do for different Actions</h5>
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
                    <ion-icon name="add" size="large" />
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
                      onActionSave();
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
                      setAdding(false);
                    }}>
                    <ion-icon
                      name="close"
                      size="large"
                      className="ion-icon-white"
                    />
                  </Button>
                </td>
                <ActionPerformerColumns
                  name={newAction.name}
                  type={newAction.config_subtype}
                  params={newAction.fields}
                  editing
                  onChange={onNewActionChange}
                  canNotDeleteOrUpdateName={false}
                />
              </tr>
              {performers.length === 0
                ? null
                : performers.map(performer => (
                    <ActionPerformerRows
                      key={performer.name}
                      name={performer.name}
                      type={performer.type}
                      params={performer.params}
                      edit={false}
                      onSave={onActionUpdate}
                      onDelete={onActionDelete}
                      canNotDeleteOrUpdateName={
                        actionRulesDependentActions.indexOf(performer.name) >= 0
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
