/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

/* eslint-disable react/prop-types */

import React, {useState} from 'react';
import Button from 'react-bootstrap/Button';
import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Form from 'react-bootstrap/Form';
import Modal from 'react-bootstrap/Modal';
import Row from 'react-bootstrap/Row';
import Table from 'react-bootstrap/Table';
import Toast from 'react-bootstrap/Toast';

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

function ActionRuleFormColumns(props) {
  const {
    name,
    mustHaveLabels,
    mustNotHaveLabels,
    action,
    showErrors,
    nameIsUnique,
    oldName,
    onChange,
  } = props;

  const actionOptions = actions.map(actn => (
    <option key={actn.id} value={actn.id}>
      {actn.name}
    </option>
  ));

  return (
    <>
      <td>
        <Form.Label>
          Name
          <span hidden={!showErrors || name}> (required)</span>
        </Form.Label>
        <Form.Control
          type="text"
          required
          value={name}
          onChange={e => onChange({name: e.target.value})}
          isInvalid={showErrors && !name}
        />
        <Form.Text
          hidden={!showErrors || nameIsUnique(name, oldName)}
          className="text-danger">
          An action rule&rsquo;s name must be unique.
        </Form.Text>
      </td>
      <td>
        <Form.Label>
          Labeled As
          <span hidden={!showErrors || mustHaveLabels}> (required)</span>
        </Form.Label>
        <Form.Control
          as="textarea"
          rows={4}
          required
          value={mustHaveLabels}
          onChange={e => onChange({must_have_labels: e.target.value})}
          isInvalid={showErrors && !mustHaveLabels}
        />
      </td>
      <td>
        <Form.Label>Not Labeled As</Form.Label>
        <Form.Control
          as="textarea"
          rows={4}
          value={mustNotHaveLabels}
          onChange={e => onChange({must_not_have_labels: e.target.value})}
        />
      </td>
      <td>
        <Form.Label>
          Action
          <span hidden={!showErrors || action !== '0'}> (required)</span>
        </Form.Label>
        <Form.Control
          as="select"
          required
          value={action}
          onChange={e => onChange({action_id: e.target.value})}
          isInvalid={showErrors && action === '0'}>
          <option value="0" key="0">
            Select an action...
          </option>
          {actionOptions}
        </Form.Control>
      </td>
    </>
  );
}

export default function ActionRuleSettingsTab() {
  const [actionRules, setActionRules] = useState(mockedActionRules);
  const [adding, setAdding] = useState(false);
  const [newActionRule, setNewActionRule] = useState({
    name: '',
    must_have_labels: '',
    must_not_have_labels: '',
    action_id: '0',
  });
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
    setNewActionRule({
      name: '',
      must_have_labels: '',
      must_not_have_labels: '',
      action_id: '0',
    });
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
    <>
      <Container>
        <Row className="mt-3">
          <Col>
            <h1>Action Rules</h1>
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
                      onClick={() => {
                        setAdding(true);
                      }}>
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
                    name={newActionRule.name}
                    mustHaveLabels={newActionRule.must_have_labels}
                    mustNotHaveLabels={newActionRule.must_not_have_labels}
                    action={newActionRule.action_id}
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
      </Container>
    </>
  );
}

function ActionRulesTableRow(props) {
  const {
    name,
    mustHaveLabels,
    mustNotHaveLabels,
    actionId,
    onDeleteActionRule,
    onUpdateActionRule,
    ruleIsValid,
    nameIsUnique,
  } = props;
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

  return (
    <>
      <tr hidden={editing}>
        <td>
          <Button
            className="mb-2 table-action-button"
            onClick={() => {
              setEditing(true);
            }}>
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
        <td>{actions.find(action => action.id === actionId).name}</td>
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
                resetForm();
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
          name={updatedActionRule.name}
          mustHaveLabels={updatedActionRule.must_have_labels}
          mustNotHaveLabels={updatedActionRule.must_not_have_labels}
          action={updatedActionRule.action_id}
          showErrors={showErrors}
          nameIsUnique={nameIsUnique}
          oldName={name}
          onChange={onUpdatedActionRuleChange}
        />
      </tr>
    </>
  );
}
