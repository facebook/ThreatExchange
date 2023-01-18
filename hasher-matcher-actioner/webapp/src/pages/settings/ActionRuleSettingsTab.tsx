/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

/* eslint-disable react/prop-types */

import Button from 'react-bootstrap/Button';
import Col from 'react-bootstrap/Col';
import React, {useContext, useState} from 'react';
import Row from 'react-bootstrap/Row';
import Table from 'react-bootstrap/Table';
import {IonIcon} from '@ionic/react';
import {add, checkmark, close} from 'ionicons/icons';
import ActionRuleFormColumns, {
  classificationTypeTBD,
} from '../../components/settings/ActionRuleFormColumns';
import ActionRulesTableRow from '../../components/settings/ActionRulesTableRow';
import '../../styles/_settings.scss';
import {addActionRule, deleteActionRule, updateActionRule} from '../../Api';
import {ActionPerformer} from './ActionPerformerSettingsTab';
import SettingsTabPane from './SettingsTabPane';
import {NotificationsContext} from '../../AppWithNotifications';

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

  classification_conditions: ClassificationCondition[];

  action_name: string;

  constructor(
    name: string,
    action_name: string,
    must_have_labels: Label[],
    must_not_have_labels: Label[],
  ) {
    this.name = name;
    this.action_name = action_name;
    this.must_have_labels = must_have_labels;
    this.must_not_have_labels = must_not_have_labels;

    this.classification_conditions = ActionRule.classificationsFromLabels(
      this.must_have_labels,
      this.must_not_have_labels,
    );
  }

  copyAndProcessUpdate = (
    update_name: 'name' | 'action_name' | 'classification_conditions',
    new_value: ClassificationCondition[] | string,
  ): ActionRule => {
    const must_have_labels =
      update_name === 'classification_conditions'
        ? ActionRule.mustHaveLabelsFromClassifications(
            new_value as ClassificationCondition[],
          )
        : this.must_have_labels;

    const must_not_have_labels =
      update_name === 'classification_conditions'
        ? ActionRule.mustNotHaveLabelsFromClassifications(
            new_value as ClassificationCondition[],
          )
        : this.must_not_have_labels;

    return new ActionRule(
      update_name === 'name' ? (new_value as string) : this.name,
      update_name === 'action_name' ? (new_value as string) : this.action_name,
      must_have_labels,
      must_not_have_labels,
    );
  };

  static mustHaveLabelsFromClassifications = (
    classification_conditions: ClassificationCondition[],
  ): Label[] =>
    classification_conditions
      .filter(classification => classification.equalTo)
      .map(classification => ({
        key: classification.classificationType,
        value: classification.classificationValue,
      }));

  static mustNotHaveLabelsFromClassifications = (
    classification_conditions: ClassificationCondition[],
  ): Label[] =>
    classification_conditions
      .filter(classification => !classification.equalTo)
      .map(classification => ({
        key: classification.classificationType,
        value: classification.classificationValue,
      }));

  static classificationsFromLabels = (
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

const defaultActionRule = new ActionRule(
  '',
  '',
  [{key: classificationTypeTBD, value: ''}],
  [],
);

type Input = {
  actions: ActionPerformer[];
  actionRules: ActionRule[];
  setActionRules: (actionRules: ActionRule[]) => void;
};

export default function ActionRuleSettingsTab({
  actions,
  actionRules,
  setActionRules,
}: Input): JSX.Element {
  const [adding, setAdding] = useState(false);
  const [newActionRule, setNewActionRule] = useState(defaultActionRule);
  const [showErrors, setShowErrors] = useState(false);
  const notifications = useContext(NotificationsContext);

  const onNewActionRuleChange = (
    update_name: 'name' | 'action_name' | 'classification_conditions',
    new_value: ClassificationCondition[] | string,
  ) => {
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
      actionRule.action_name !== defaultActionRule.action_name &&
      actionRuleNameIsUnique(actionRule.name, oldName)) as boolean;

  const ruleIsValid = (actionRule: ActionRule, oldName: string) =>
    actionRuleIsValid(actionRule, oldName);

  const resetForm = () => {
    setNewActionRule(defaultActionRule);
  };

  const onAddActionRule = (actionRule: ActionRule, addToUIOnly: boolean) => {
    actionRules.push(actionRule);
    actionRules.sort((a, b) =>
      a.name.toLowerCase() > b.name.toLowerCase() ? 1 : -1,
    );
    setActionRules([...actionRules]);
    if (!addToUIOnly) {
      addActionRule(actionRule);
      notifications.success({
        message: 'A new action rule was added successfully.',
      });
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
      notifications.success({
        message: 'The action rule was deleted successfully.',
      });
    }
  };

  const onUpdateActionRule = (
    oldName: string,
    updatedActionRule: ActionRule,
  ) => {
    onDeleteActionRule(oldName, true); // deleteFromUIOnly
    onAddActionRule(updatedActionRule, true); // addToUIOnly
    updateActionRule(oldName, updatedActionRule);
    notifications.success({
      message: 'The action rule was updated successfully.',
    });
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
    <SettingsTabPane>
      <Row>
        <Col>
          <SettingsTabPane.Title>Action Rules</SettingsTabPane.Title>
        </Col>
      </Row>
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
                    <IonIcon icon={add} size="large" />
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
                    <IonIcon icon={checkmark} size="large" color="white" />
                  </Button>{' '}
                  <Button
                    variant="outline-secondary"
                    className="table-action-button"
                    onClick={() => {
                      setShowErrors(false);
                      resetForm();
                      setAdding(false);
                    }}>
                    <IonIcon icon={close} size="large" color="white" />
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
    </SettingsTabPane>
  );
}
