/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React, {useState} from 'react';
import {IonIcon} from '@ionic/react';
import {close, trashBin, pencil, checkmark} from 'ionicons/icons';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';

import ActionRuleFormColumns from './ActionRuleFormColumns';
import '../../styles/_settings.scss';
import type {
  ActionRule,
  ClassificationCondition,
} from '../../pages/settings/ActionRuleSettingsTab';
import {ActionPerformer} from '../../pages/settings/ActionPerformerSettingsTab';

type Input = {
  actionRule: ActionRule;
  actions: ActionPerformer[];
  onDeleteActionRule: (name: string, deleteFromUIOnly: boolean) => void;
  onUpdateActionRule: (oldName: string, updatedActionRule: ActionRule) => void;
  ruleIsValid: (actionRule: ActionRule, oldName: string) => boolean;
  nameIsUnique: (newName: string, oldName: string) => boolean;
};

export default function ActionRulesTableRow({
  actionRule,
  actions,
  onDeleteActionRule,
  onUpdateActionRule,
  ruleIsValid,
  nameIsUnique,
}: Input): JSX.Element {
  const [editing, setEditing] = useState(false);
  const [
    showDeleteActionRuleConfirmation,
    setShowDeleteActionRuleConfirmation,
  ] = useState(false);

  const [updatedActionRule, setUpdatedActionRule] = useState(actionRule);
  const [showErrors, setShowErrors] = useState(false);

  const onUpdatedActionRuleChange = (
    update_name: 'name' | 'action_name' | 'classification_conditions',
    new_value: string | ClassificationCondition[],
  ) => {
    const newUpdatedActionRule = updatedActionRule.copyAndProcessUpdate(
      update_name,
      new_value,
    );
    setUpdatedActionRule(newUpdatedActionRule);
  };

  const resetForm = () => {
    setUpdatedActionRule(actionRule);
  };

  const getAction = () => {
    if (
      actions === undefined ||
      actions.length === 0 ||
      actionRule.action_name === undefined ||
      actionRule.action_name.length === 0
    ) {
      return <span>&mdash;</span>;
    }
    const actionPerformer = actions.find(
      action => action.name === actionRule.action_name,
    );
    if (actionPerformer) {
      return actionPerformer.name;
    }
    return <span>&mdash;</span>;
  };

  const getClassificationDescriptions = () => {
    if (
      updatedActionRule.classification_conditions === undefined ||
      updatedActionRule.classification_conditions.length === 0
    ) {
      return 'No Rules defined';
    }
    const classificationDescriptions =
      updatedActionRule.classification_conditions.map(classification => {
        let ret = 'the';
        switch (classification.classificationType) {
          case 'BankSourceClassification':
            ret += ' Dataset Source';
            break;
          case 'BankIDClassification':
            ret += ' Dataset ID';
            break;

          case 'BankedContentIDClassification':
            ret += ' MatchedContent ID';
            break;

          case 'Classification':
            ret += ' MatchedContent';
            break;
          case 'SubmittedContent':
            ret += ' SubmittedContent';
            break;
          default:
            ret += ` ${classification.classificationType}`;
            break;
        }

        if (classification.equalTo) {
          ret +=
            classification.classificationType === 'Classification' ||
            classification.classificationType === 'SubmittedContent'
              ? ' has been classified'
              : ' is';
        } else {
          ret +=
            classification.classificationType === 'Classification' ||
            classification.classificationType === 'SubmittedContent'
              ? ' has not been classified'
              : ' is not';
        }
        ret += ` ${classification.classificationValue}`;
        return ret;
      });
    return `Run the action if ${classificationDescriptions.join('; and ')}`;
  };

  return (
    <>
      <tr hidden={editing}>
        <td>
          <Button
            className="mb-2 table-action-button"
            onClick={() => setEditing(true)}>
            <IonIcon icon={pencil} size="large" color="white" />
          </Button>{' '}
          <Modal
            show={showDeleteActionRuleConfirmation}
            onHide={() => setShowDeleteActionRuleConfirmation(false)}>
            <Modal.Header closeButton>
              <Modal.Title>Confirm Action Rule Delete</Modal.Title>
            </Modal.Header>
            <Modal.Body>
              <p>
                Please confirm you want to delete the action rule named{' '}
                <strong>{actionRule.name}</strong>.
              </p>
            </Modal.Body>
            <Modal.Footer>
              <Button
                variant="secondary"
                onClick={() => setShowDeleteActionRuleConfirmation(false)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={() => onDeleteActionRule(actionRule.name, false)}>
                Yes, Delete This Action Rule
              </Button>
            </Modal.Footer>
          </Modal>
        </td>
        <td>{actionRule.name}</td>
        <td className="action-rule-classification-column">
          {getClassificationDescriptions()}
        </td>
        <td>{getAction()}</td>
      </tr>
      <tr hidden={!editing}>
        <td>
          <Button
            variant="outline-primary"
            className="mb-2 table-action-button"
            onClick={() => {
              setShowErrors(false);
              if (ruleIsValid(updatedActionRule, actionRule.name)) {
                onUpdateActionRule(actionRule.name, updatedActionRule);
                setEditing(false);
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
              setEditing(false);
            }}>
            <IonIcon icon={close} size="large" color="white" />
          </Button>
          <hr />
          <Button
            variant="secondary"
            className="mb-2 table-action-button"
            onClick={() => setShowDeleteActionRuleConfirmation(true)}>
            <IonIcon icon={trashBin} size="large" className="white" />
          </Button>
        </td>
        <ActionRuleFormColumns
          actions={actions}
          actionRule={updatedActionRule}
          showErrors={showErrors}
          nameIsUnique={nameIsUnique}
          oldName={actionRule.name}
          onChange={onUpdatedActionRuleChange}
        />
      </tr>
    </>
  );
}
