/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState} from 'react';
import {PropTypes} from 'prop-types';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import ActionRuleFormColumns from './ActionRuleFormColumns';
import '../../styles/_settings.scss';

const classificationsFromLabels = (mustHaveLabels, mustNotHaveLabels) =>
  mustHaveLabels
    .map(mustHaveLabel => ({
      classification_type: mustHaveLabel.key,
      equals: true,
      classification_value: mustHaveLabel.value,
    }))
    .concat(
      mustNotHaveLabels.map(mustNotHaveLabel => ({
        classification_type: mustNotHaveLabel.key,
        equals: false,
        classification_value: mustNotHaveLabel.value,
      })),
    );
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
    classifications: classificationsFromLabels(
      mustHaveLabels,
      mustNotHaveLabels,
    ),
    action_id: actionId,
  });
  const [showErrors, setShowErrors] = useState(false);

  const onUpdatedActionRuleChange = updatedField => {
    setUpdatedActionRule({...updatedActionRule, ...updatedField});
  };

  const resetForm = () => {
    setUpdatedActionRule({
      name,
      classifications: classificationsFromLabels(
        mustHaveLabels,
        mustNotHaveLabels,
      ),
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
    const actionPerformer = actions.find(action => action.id === actionId);
    if (actionPerformer) {
      return actionPerformer.name;
    }
    return <span>&mdash;</span>;
  };

  const getClassificationDescriptions = () => {
    const classificationDescriptions = updatedActionRule.classifications.map(
      classification => {
        let ret = 'the';
        switch (classification.classification_type) {
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
            ret += ` ${classification.classification_type}`;
            break;
        }

        if (classification.equals) {
          ret +=
            classification.classification_type === 'Classification'
              ? ' has been classified'
              : ' is';
        } else {
          ret +=
            classification.classification_type === 'Classification'
              ? ' has not been classified'
              : ' is not';
        }
        ret += ` ${classification.classification_value}`;
        return ret;
      },
    );
    return `Run the action if ${classificationDescriptions.join('; and ')}`;
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

              // Convert classifications into Label sets which the backend understands
              const updatedMustHaveLabels = updatedActionRule.classifications
                .filter(classification => classification.equals)
                .map(classification => ({
                  key: classification.classification_type,
                  value: classification.classification_value,
                }));
              const updatedMustNotHaveLabels = updatedActionRule.classifications
                .filter(classification => !classification.equals)
                .map(classification => ({
                  key: classification.classification_type,
                  value: classification.classification_value,
                }));

              updatedActionRule.must_have_labels = updatedMustHaveLabels;
              updatedActionRule.must_not_have_labels = updatedMustNotHaveLabels;
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
          classifications={updatedActionRule.classifications}
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
  mustHaveLabels: PropTypes.arrayOf(
    PropTypes.shape({
      key: PropTypes.string.isRequired,
      value: PropTypes.string.isRequired,
    }),
  ).isRequired,
  mustNotHaveLabels: PropTypes.arrayOf(
    PropTypes.shape({
      key: PropTypes.string.isRequired,
      value: PropTypes.string.isRequired,
    }),
  ),
  actionId: PropTypes.string.isRequired,
  onDeleteActionRule: PropTypes.func.isRequired,
  onUpdateActionRule: PropTypes.func.isRequired,
  ruleIsValid: PropTypes.func.isRequired,
  nameIsUnique: PropTypes.func.isRequired,
};

ActionRulesTableRow.defaultProps = {
  mustNotHaveLabels: '',
};
