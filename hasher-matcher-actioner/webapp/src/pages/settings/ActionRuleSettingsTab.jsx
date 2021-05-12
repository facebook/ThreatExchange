/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

/* eslint-disable react/prop-types */

import Button from 'react-bootstrap/Button';
import Col from 'react-bootstrap/Col';
import React, {useState} from 'react';
import Row from 'react-bootstrap/Row';
import Table from 'react-bootstrap/Table';
import Toast from 'react-bootstrap/Toast';
import ActionRuleFormColumns from '../../components/settings/ActionRuleFormColumns';
import ActionRulesTableRow from '../../components/settings/ActionRulesTableRow';
import '../../styles/_settings.scss';
import FixedWidthCenterAlignedLayout from '../layouts/FixedWidthCenterAlignedLayout';

const mockedActionRules = [
  {
    name: 'Bank ID 303636684709969 Except Sailboat',
    must_have_labels:
      'BankIDClassificationLabel(303636684709969), ClassificationLabel(true_positive)',
    must_not_have_labels:
      'BankedContentIDClassificationLabel(3364504410306721)',
    action_id: '1',
  },
  {
    name: 'Bank ID 303636684709969, Sailboat',
    must_have_labels:
      'BankIDClassificationLabel(303636684709969), ClassificationLabel(true_positive), BankedContentIDClassificationLabel(3364504410306721)',
    must_not_have_labels: '',
    action_id: '2',
  },
];

const actions = [
  {
    name: 'EnqueueMiniCastleForReview',
    id: '1',
  },
  {
    name: 'EnqueueSailboatForReview',
    id: '2',
  },
];

const defaultActionRule = {
  name: '',
  must_have_labels: '',
  must_not_have_labels: '',
  action_id: '0',
};

export default function ActionRuleSettingsTab() {
  const [actionRules, setActionRules] = useState(mockedActionRules);
  const [adding, setAdding] = useState(false);
  const [newActionRule, setNewActionRule] = useState(defaultActionRule);
  const [showErrors, setShowErrors] = useState(false);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

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

  const addActionRule = actionRule => {
    actionRules.push(actionRule);
    actionRules.sort((a, b) =>
      a.name.toLowerCase() > b.name.toLowerCase() ? 1 : -1,
    );
    setActionRules([...actionRules]);
  };

  const displayToast = message => {
    setToastMessage(message);
    setShowToast(true);
  };

  const deleteActionRule = (oldName, suppressToast) => {
    const indexToDelete = actionRules.findIndex(
      actionRule => actionRule.name === oldName,
    );
    actionRules.splice(indexToDelete, 1);
    setActionRules([...actionRules]);
    if (suppressToast === undefined) {
      displayToast('The action rule was deleted successfully.');
    }
  };

  const updateActionRule = (oldName, updatedActionRule) => {
    deleteActionRule(oldName, true);
    addActionRule(updatedActionRule);
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
      onDeleteActionRule={deleteActionRule}
      onUpdateActionRule={updateActionRule}
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
                <th>Labeled As</th>
                <th>Not Labeled As</th>
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
                        addActionRule(newActionRule);
                        resetForm();
                        setAdding(false);
                        displayToast(
                          'A new action rule was added successfully.',
                        );
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
