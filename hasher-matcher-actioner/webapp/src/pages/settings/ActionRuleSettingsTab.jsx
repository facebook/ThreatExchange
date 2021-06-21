/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

/* eslint-disable react/prop-types */

import Button from 'react-bootstrap/Button';
import Col from 'react-bootstrap/Col';
import React, {useEffect, useState} from 'react';
import Row from 'react-bootstrap/Row';
import Table from 'react-bootstrap/Table';
import Toast from 'react-bootstrap/Toast';
import ActionRuleFormColumns from '../../components/settings/ActionRuleFormColumns';
import ActionRulesTableRow from '../../components/settings/ActionRulesTableRow';
import '../../styles/_settings.scss';
import FixedWidthCenterAlignedLayout from '../layouts/FixedWidthCenterAlignedLayout';
import {
  addActionRule,
  deleteActionRule,
  fetchAllActions,
  fetchAllActionRules,
  updateActionRule,
} from '../../Api';

const defaultActionRule = {
  name: '',
  must_have_labels: '',
  must_not_have_labels: '',
  action_id: '0',
};

export default function ActionRuleSettingsTab() {
  const [actionRules, setActionRules] = useState([]);
  const [actions, setActions] = useState([]);
  const [adding, setAdding] = useState(false);
  const [newActionRule, setNewActionRule] = useState(defaultActionRule);
  const [showErrors, setShowErrors] = useState(false);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  useEffect(() => {
    fetchAllActionRules().then(response => {
      if (response && response.error_message === '') {
        const mappedActionRules = response.action_rules.map(actionRule => ({
          name: actionRule.name,
          must_have_labels: actionRule.must_have_labels,
          must_not_have_labels: actionRule.must_not_have_labels,
          action_id: actionRule.action_label.value,
        }));
        setActionRules(mappedActionRules);
      }
    });
  }, []);

  useEffect(() => {
    fetchAllActions().then(response => {
      if (response) {
        const actns = response.actions_response.map(action => ({
          name: action.name,
          id: action.name,
        }));
        setActions(actns);
      }
    });
  }, []);

  const onNewActionRuleChange = updatedField => {
    setNewActionRule({...newActionRule, ...updatedField});
  };

  const actionRuleNameIsUnique = (newName, oldName, actionrules) => {
    if (newName) {
      const nameLower = newName.toLowerCase();

      const actionRuleIndex = actionrules.findIndex(
        actionRule => actionRule.name.toLowerCase() === nameLower,
      );

      return actionRuleIndex === -1 ? true : newName === oldName;
    }
    return true;
  };

  const nameIsUnique = (newName, oldName) =>
    actionRuleNameIsUnique(newName, oldName, actionRules);

  const actionRuleIsValid = (actionRule, actionrules, oldName) =>
    actionRule.name &&
    actionRule.must_have_labels &&
    actionRule.action_id !== '0' &&
    actionRuleNameIsUnique(actionRule.name, oldName, actionrules);

  const ruleIsValid = (actionRule, oldName) =>
    actionRuleIsValid(actionRule, actionRules, oldName);

  const resetForm = () => {
    setNewActionRule(defaultActionRule);
  };

  const displayToast = message => {
    setToastMessage(message);
    setShowToast(true);
  };

  const getAPIActionRule = actionRule => ({
    name: actionRule.name,
    must_have_labels: actionRule.must_have_labels,
    must_not_have_labels: actionRule.must_not_have_labels,
    action_label: {
      key: 'Action',
      value: actionRule.action_id,
    },
  });

  const onAddActionRule = (actionRule, addToUIOnly) => {
    actionRules.push(actionRule);
    actionRules.sort((a, b) =>
      a.name.toLowerCase() > b.name.toLowerCase() ? 1 : -1,
    );
    setActionRules([...actionRules]);
    if (addToUIOnly === undefined) {
      const apiActionRule = getAPIActionRule(actionRule);
      addActionRule(apiActionRule);
      displayToast('A new action rule was added successfully.');
    }
  };

  const onDeleteActionRule = (name, deleteFromUIOnly) => {
    const indexToDelete = actionRules.findIndex(
      actionRule => actionRule.name === name,
    );
    actionRules.splice(indexToDelete, 1);
    setActionRules([...actionRules]);
    if (deleteFromUIOnly === undefined) {
      deleteActionRule(name);
      displayToast('The action rule was deleted successfully.');
    }
  };

  const onUpdateActionRule = (oldName, updatedActionRule) => {
    onDeleteActionRule(oldName, true); // deleteFromUIOnly
    onAddActionRule(updatedActionRule, true); // addToUIOnly
    const apiActionRule = getAPIActionRule(updatedActionRule);
    updateActionRule(oldName, apiActionRule);
    displayToast('The action rule was updated successfully.');
  };

  const actionRulesTableRows = actionRules.map(actionRule => (
    <ActionRulesTableRow
      key={actionRule.name}
      actions={actions}
      name={actionRule.name}
      mustHaveLabels={actionRule.must_have_labels}
      mustNotHaveLabels={actionRule.must_not_have_labels}
      actionId={actionRule.action_id}
      onDeleteActionRule={onDeleteActionRule}
      onUpdateActionRule={onUpdateActionRule}
      ruleIsValid={ruleIsValid}
      nameIsUnique={nameIsUnique}
    />
  ));

  return (
    <FixedWidthCenterAlignedLayout title="Action Rules">
      <Row className="mt-3">
        <Col>
          <p>
            Each rule indicates an action to be taken based on labels (e.g.,
            classification labels of a matching signal)
          </p>
        </Col>
      </Row>
      <Row>
        <Col>
          <Table bordered>
            <thead>
              <tr>
                <th>
                  <Button
                    className="table-action-button"
                    onClick={() => setAdding(true)}>
                    <ion-icon name="add" size="large" />
                  </Button>
                </th>
                <th>Name</th>
                <th>Classifications</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              <tr hidden={!adding}>
                <td>
                  <Button
                    variant="outline-primary"
                    className="mb-2 table-action-button"
                    onClick={() => {
                      setShowErrors(false);
                      if (actionRuleIsValid(newActionRule, actionRules)) {
                        onAddActionRule(newActionRule);
                        resetForm();
                        setAdding(false);
                      } else {
                        setShowErrors(true);
                      }
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
                      setShowErrors(false);
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
                <ActionRuleFormColumns
                  actions={actions}
                  name={newActionRule.name}
                  mustHaveLabels={newActionRule.must_have_labels}
                  mustNotHaveLabels={newActionRule.must_not_have_labels}
                  actionId={newActionRule.action_id}
                  showErrors={showErrors}
                  nameIsUnique={nameIsUnique}
                  oldName={undefined}
                  onChange={onNewActionRuleChange}
                />
              </tr>
              {actionRulesTableRows}
            </tbody>
          </Table>
        </Col>
      </Row>
      <div className="feedback-toast-container">
        <Toast
          onClose={() => setShowToast(false)}
          show={showToast}
          delay={5000}
          autohide>
          <Toast.Body>{toastMessage}</Toast.Body>
        </Toast>
      </div>
    </FixedWidthCenterAlignedLayout>
  );
}
