/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState} from 'react';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';

import ActionRuleFormColumns from './ActionRuleFormColumns';
import '../../styles/_settings.scss';
import type {
  Action,
  ActionRule,
} from '../../pages/settings/ActionRuleSettingsTab';

type Input = {
  actionRule: ActionRule;
  actions: Action[];
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

  const onUpdatedActionRuleChange = (update_name: string, new_value: any) => {
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
      actionRule.action_id === undefined ||
      actionRule.action_id.length === 0
    ) {
      return <span>&mdash;</span>;
    }
    const actionPerformer = actions.find(
      action => action.id === actionRule.action_id,
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
          default:
            ret += ` ${classification.classificationType}`;
            break;
        }

        if (classification.equalTo) {
          ret +=
            classification.classificationType === 'Classification'
              ? ' has been classified'
              : ' is';
        } else {
          ret +=
            classification.classificationType === 'Classification'
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
            {/* @ts-expect-error TODO: ts doenst recognize that ion-icon has been imported */}

            <ion-icon name="pencil" size="large" className="ion-icon-white" />
          </Button>{' '}
          <Button
            variant="secondary"
            className="table-action-button"
            onClick={() => setShowDeleteActionRuleConfirmation(true)}>
            {/* @ts-expect-error TODO: ts doenst recognize that ion-icon has been imported */}
            <ion-icon
              name="trash-bin"
              size="large"
              className="ion-icon-white"
            />
          </Button>
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
              setEditing(false);
            }}>
            {/* @ts-expect-error TODO: ts doenst recognize that ion-icon has been imported */}
            <ion-icon name="close" size="large" className="ion-icon-white" />
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
