/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState} from 'react';
import {PropTypes} from 'prop-types';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import ActionRuleFormColumns from './ActionRuleFormColumns';
import '../../styles/_settings.scss';

export default function ActionRulesTableRow({
  actions,
  name,
  mustHaveLabels,
  mustNotHaveLabels,
  actionId,
  onDeleteActionRule,
  onUpdateActionRule,
  ruleIsValid,
  nameIsUnique,
}) {
  const [editing, setEditing] = useState(false);
  const [
    showDeleteActionRuleConfirmation,
    setShowDeleteActionRuleConfirmation,
  ] = useState(false);
  const [updatedActionRule, setUpdatedActionRule] = useState({
    name,
    must_have_labels: mustHaveLabels,
    must_not_have_labels: mustNotHaveLabels,
    action_id: actionId,
  });
  const [showErrors, setShowErrors] = useState(false);

  const onUpdatedActionRuleChange = updatedField => {
    setUpdatedActionRule({...updatedActionRule, ...updatedField});
  };

  const resetForm = () => {
    setUpdatedActionRule({
      name,
      must_have_labels: mustHaveLabels,
      must_not_have_labels: mustNotHaveLabels,
      action_id: actionId,
    });
  };

  const getAction = () => {
    if (
      actions === undefined ||
      actions.length === 0 ||
      actionId === undefined ||
      actionId.length === 0
    ) {
      return <span>&mdash;</span>;
    }
    return actions.find(action => action.id === actionId).name;
  };

  return (
    <>
      <tr hidden={editing}>
        <td>
          <Button
            className="mb-2 table-action-button"
            onClick={() => setEditing(true)}>
            <ion-icon name="pencil" size="large" className="ion-icon-white" />
          </Button>{' '}
          <Button
            variant="secondary"
            className="table-action-button"
            onClick={() => setShowDeleteActionRuleConfirmation(true)}>
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
                <strong>{name}</strong>.
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
                onClick={() => onDeleteActionRule(name)}>
                Yes, Delete This Action Rule
              </Button>
            </Modal.Footer>
          </Modal>
        </td>
        <td>{name}</td>
        <td className="action-rule-classification-column">{mustHaveLabels}</td>
        <td className="action-rule-classification-column">
          {mustNotHaveLabels.length > 0 ? (
            mustNotHaveLabels
          ) : (
            <span>&mdash;</span>
          )}
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
              if (ruleIsValid(updatedActionRule, name)) {
                onUpdateActionRule(name, updatedActionRule);
                setEditing(false);
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
              setEditing(false);
            }}>
            <ion-icon name="close" size="large" className="ion-icon-white" />
          </Button>
        </td>
        <ActionRuleFormColumns
          actions={actions}
          name={updatedActionRule.name}
          mustHaveLabels={updatedActionRule.must_have_labels}
          mustNotHaveLabels={updatedActionRule.must_not_have_labels}
          actionId={updatedActionRule.action_id}
          showErrors={showErrors}
          nameIsUnique={nameIsUnique}
          oldName={name}
          onChange={onUpdatedActionRuleChange}
        />
      </tr>
    </>
  );
}

ActionRulesTableRow.propTypes = {
  actions: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
    }),
  ).isRequired,
  name: PropTypes.string.isRequired,
  mustHaveLabels: PropTypes.string.isRequired,
  mustNotHaveLabels: PropTypes.string,
  actionId: PropTypes.string.isRequired,
  onDeleteActionRule: PropTypes.func.isRequired,
  onUpdateActionRule: PropTypes.func.isRequired,
  ruleIsValid: PropTypes.func.isRequired,
  nameIsUnique: PropTypes.func.isRequired,
};

ActionRulesTableRow.defaultProps = {
  mustNotHaveLabels: '',
};
