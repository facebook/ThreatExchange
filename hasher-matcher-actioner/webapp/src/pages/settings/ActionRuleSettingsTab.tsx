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

import ActionRuleFormColumns, {
  classificationTypeTBD,
} from '../../components/settings/ActionRuleFormColumns';
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

export type Label = {
  key: string;
  value: string;
};

export type ClassificationCondition = {
  classificationType: string;
  classificationValue: string;
  equalTo: boolean;
};

export class ActionRule {
  name: string;

  must_have_labels: Label[];

  must_not_have_labels: Label[];

  action_id: string;

  classification_conditions: ClassificationCondition[];

  constructor(
    name: string,
    must_have_labels: Label[],
    must_not_have_labels: Label[],
    action_id: string,
  ) {
    this.name = name;
    this.must_have_labels = must_have_labels;
    this.must_not_have_labels = must_not_have_labels;
    this.action_id = action_id;

    this.classification_conditions = this.classificationsFromLabels(
      this.must_have_labels,
      this.must_not_have_labels,
    );
  }

  copyAndProcessUpdate = (update_name: string, new_value: any): ActionRule => {
    if (
      !['name', 'action_id', 'classification_conditions'].includes(update_name)
    ) {
      throw Error(`Unknown ActionRule update: ${update_name}`);
    }

    const must_have_labels =
      update_name === 'classification_conditions'
        ? this.mustHaveLabelsFromClassifications(new_value)
        : this.must_have_labels;

    const must_not_have_labels =
      update_name === 'classification_conditions'
        ? this.mustNotHaveLabelsFromClassifications(new_value)
        : this.must_not_have_labels;

    return new ActionRule(
      update_name === 'name' ? new_value : this.name,
      must_have_labels,
      must_not_have_labels,
      update_name === 'action_id' ? new_value : this.action_id,
    );
  };

  mustHaveLabelsFromClassifications = (
    classification_conditions: ClassificationCondition[],
  ): Label[] =>
    classification_conditions
      .filter(classification => classification.equalTo)
      .map(classification => ({
        key: classification.classificationType,
        value: classification.classificationValue,
      }));

  mustNotHaveLabelsFromClassifications = (
    classification_conditions: ClassificationCondition[],
  ): Label[] =>
    classification_conditions
      .filter(classification => !classification.equalTo)
      .map(classification => ({
        key: classification.classificationType,
        value: classification.classificationValue,
      }));

  classificationsFromLabels = (
    mustHaveLabels: Label[],
    mustNotHaveLabels: Label[],
  ): ClassificationCondition[] =>
    mustHaveLabels
      .map(mustHaveLabel => ({
        classificationType: mustHaveLabel.key,
        equalTo: true,
        classificationValue: mustHaveLabel.value,
      }))
      .concat(
        mustNotHaveLabels.map(mustNotHaveLabel => ({
          classificationType: mustNotHaveLabel.key,
          equalTo: false,
          classificationValue: mustNotHaveLabel.value,
        })),
      );
}

export type Action = {
  name: string;
  id: string;
};

const defaultActionRule = new ActionRule(
  '',
  [{key: classificationTypeTBD, value: ''}],
  [],
  '0',
);

const defaultActionRules: ActionRule[] = [];

export default function ActionRuleSettingsTab(): JSX.Element {
  const [actionRules, setActionRules] =
    useState<ActionRule[]>(defaultActionRules);
  const [actions, setActions] = useState<Action[]>([]);
  const [adding, setAdding] = useState(false);
  const [newActionRule, setNewActionRule] = useState(defaultActionRule);
  const [showErrors, setShowErrors] = useState(false);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  useEffect(() => {
    fetchAllActionRules().then(response => {
      if (response && response.error_message === '') {
        const mappedActionRules = response.action_rules.map(
          (actionRule: {
            name: string;
            must_have_labels: Label[];
            must_not_have_labels: Label[];
            action_label: Label;
          }) =>
            new ActionRule(
              actionRule.name,
              actionRule.must_have_labels,
              actionRule.must_not_have_labels,
              actionRule.action_label.value,
            ),
        );
        setActionRules(mappedActionRules);
      }
    });
  }, []);

  useEffect(() => {
    fetchAllActions().then(response => {
      if (response) {
        const actns = response.actions_response.map((action: Action) => ({
          name: action.name,
          id: action.name,
        }));
        setActions(actns);
      }
    });
  }, []);

  const onNewActionRuleChange = (update_name: string, new_value: any) => {
    const newNewActionRule = newActionRule.copyAndProcessUpdate(
      update_name,
      new_value,
    );
    setNewActionRule(newNewActionRule);
  };

  const actionRuleNameIsUnique = (newName: string, oldName: string) => {
    if (newName) {
      const nameLower = newName.toLowerCase();

      const actionRuleIndex = actionRules.findIndex(
        actionRule => actionRule.name.toLowerCase() === nameLower,
      );

      return actionRuleIndex === -1 ? true : newName === oldName;
    }
    return true;
  };

  const nameIsUnique = (newName: string, oldName: string) =>
    actionRuleNameIsUnique(newName, oldName);

  const actionRuleIsValid = (actionRule: ActionRule, oldName: string) =>
    (actionRule.name &&
      actionRule.must_have_labels.length &&
      actionRule.must_have_labels.every(
        label => label.key !== classificationTypeTBD && label.value,
      ) &&
      actionRule.must_not_have_labels.every(
        label => label.key !== classificationTypeTBD && label.value,
      ) &&
      actionRule.action_id !== '0' &&
      actionRuleNameIsUnique(actionRule.name, oldName)) as boolean;

  const ruleIsValid = (actionRule: ActionRule, oldName: string) =>
    actionRuleIsValid(actionRule, oldName);

  const resetForm = () => {
    setNewActionRule(defaultActionRule);
  };

  const displayToast = (message: string) => {
    setToastMessage(message);
    setShowToast(true);
  };

  const getAPIActionRule = (actionRule: ActionRule) => ({
    name: actionRule.name,
    must_have_labels: actionRule.must_have_labels,
    must_not_have_labels: actionRule.must_not_have_labels,
    action_label: {
      key: 'Action',
      value: actionRule.action_id,
    },
  });

  const onAddActionRule = (actionRule: ActionRule, addToUIOnly: boolean) => {
    actionRules.push(actionRule);
    actionRules.sort((a, b) =>
      a.name.toLowerCase() > b.name.toLowerCase() ? 1 : -1,
    );
    setActionRules([...actionRules]);
    if (!addToUIOnly) {
      const apiActionRule = getAPIActionRule(actionRule);
      addActionRule(apiActionRule);
      displayToast('A new action rule was added successfully.');
    }
  };

  const onDeleteActionRule = (name: string, deleteFromUIOnly: boolean) => {
    const indexToDelete = actionRules.findIndex(
      actionRule => actionRule.name === name,
    );
    actionRules.splice(indexToDelete, 1);
    setActionRules([...actionRules]);
    if (!deleteFromUIOnly) {
      deleteActionRule(name);
      displayToast('The action rule was deleted successfully.');
    }
  };

  const onUpdateActionRule = (
    oldName: string,
    updatedActionRule: ActionRule,
  ) => {
    onDeleteActionRule(oldName, true); // deleteFromUIOnly
    onAddActionRule(updatedActionRule, true); // addToUIOnly
    const apiActionRule = getAPIActionRule(updatedActionRule);
    updateActionRule(oldName, apiActionRule);
    displayToast('The action rule was updated successfully.');
  };

  const actionRulesTableRows = actionRules.map(actionRule => (
    <ActionRulesTableRow
      key={actionRule.name}
      actionRule={actionRule}
      actions={actions}
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
            ActionRules are a configurable algorithm which takes a Match and,
            based on the Classifications on the Match, determines what Actions,
            if any, should be performed as a result.
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
                    {/* @ts-expect-error TODO: ts doenst recognize that ion-icon has been imported */}
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
                      if (actionRuleIsValid(newActionRule, '')) {
                        onAddActionRule(newActionRule, false);
                        resetForm();
                        setAdding(false);
                      } else {
                        setShowErrors(true);
                      }
                    }}>
                    {/* @ts-expect-error TODO: ts doenst recognize that ion-icon has been imported */}
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
                    {/* @ts-expect-error TODO: ts doenst recognize that ion-icon has been imported */}
                    <ion-icon
                      name="close"
                      size="large"
                      className="ion-icon-white"
                    />
                  </Button>
                </td>
                <ActionRuleFormColumns
                  actions={actions}
                  actionRule={newActionRule}
                  showErrors={showErrors}
                  nameIsUnique={nameIsUnique}
                  oldName=""
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
