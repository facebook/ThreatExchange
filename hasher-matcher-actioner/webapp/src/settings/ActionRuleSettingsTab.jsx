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

function actionRuleNameIsUnique(name, actionrules) {
  if (name) {
    const nameLower = name.toLowerCase();
    return (
      actionrules.findIndex(
        actionRule => actionRule.name.toLowerCase() === nameLower,
      ) === -1
    );
  }

  return true;
}

function actionRuleIsValid(actionRule, actionrules) {
  return (
    actionRule.name &&
    actionRule.must_have_labels &&
    actionRule.action_id !== '0' &&
    actionRuleNameIsUnique(actionRule.name, actionrules)
  );
}

function Required(props) {
  const {show} = props;
  return (
    <span hidden={!show} className="text-danger">
      (required)
    </span>
  );
}

function ActionRuleFormColumns(props) {
  const {
    nameRef,
    mustHaveLabelsRef,
    mustNotHaveLabelsRef,
    actionRef,
    showNameMustBeUnique,
  } = props;

  const actionOptions = actions.map(action => (
    <option key={action.id} value={action.id}>
      {action.name}
    </option>
  ));

  return (
    <>
      <td>
        <Form.Control type="text" required ref={nameRef} />
        <Form.Text hidden={!showNameMustBeUnique} className="text-danger">
          An action rule&rsquo;s name must be unique.
        </Form.Text>
      </td>
      <td>
        <Form.Control as="textarea" rows={4} required ref={mustHaveLabelsRef} />
      </td>
      <td>
        <Form.Control as="textarea" rows={4} ref={mustNotHaveLabelsRef} />
      </td>
      <td>
        <Form.Control as="select" required ref={actionRef}>
          <option value="0" key="0" selected>
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
  const [nameRef] = useState(React.createRef());
  const [mustHaveLabelsRef] = useState(React.createRef());
  const [mustNotHaveLabelsRef] = useState(React.createRef());
  const [actionRef] = useState(React.createRef());
  const [showNameRequired, setShowNameRequired] = useState(false);
  const [showNameMustBeUnique, setShowNameMustBeUnique] = useState(false);
  const [showMustHaveLabelsRequired, setShowMustHaveLabelsRequired] = useState(
    false,
  );
  const [showActionRequired, setShowActionRequired] = useState(false);
  const [showDeletedActionRuleToast, setShowDeletedActionRuleToast] = useState(
    false,
  );

  const resetForm = () => {
    nameRef.current.value = '';
    mustHaveLabelsRef.current.value = '';
    mustNotHaveLabelsRef.current.value = '';
    actionRef.current.value = '0';
  };

  const addActionRule = newActionRule => {
    actionRules.push(newActionRule);
    actionRules.sort((a, b) =>
      a.name.toLowerCase() > b.name.toLowerCase() ? 1 : -1,
    );
    setActionRules([...actionRules]);
  };

  const deleteActionRule = name => {
    const indexToDelete = actionRules.findIndex(
      actionRule => actionRule.name === name,
    );
    actionRules.splice(indexToDelete, 1);
    console.log(actionRules);
    setActionRules([...actionRules]);
    setShowDeletedActionRuleToast(true);
  };

  const saveActionRule = (oldName, editedActionRule) => {
    const indexToUpdate = actionRules.findIndex(
      actionRule => actionRule.name === oldName,
    );
    deleteActionRule(oldName);
    addActionRule(editedActionRule);
  };

  const actionRulesTableRows = actionRules.map(actionRule => (
    <ActionRulesTableRow
      key={actionRule.name}
      name={actionRule.name}
      mustHaveLabels={actionRule.must_have_labels}
      mustNotHaveLabels={actionRule.must_not_have_labels}
      actionId={actionRule.action_id}
      onDeleteActionRule={deleteActionRule}
      onSaveEditedActionRule={saveActionRule}
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
                  <th>
                    Name <Required show={adding && showNameRequired} />
                  </th>
                  <th>
                    Labeled As <Required show={showMustHaveLabelsRequired} />
                  </th>
                  <th>Not Labeled As</th>
                  <th>
                    Action <Required show={showActionRequired} />
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr hidden={!adding}>
                  <td>
                    <Button
                      variant="outline-primary"
                      className="mb-2 table-action-button"
                      onClick={() => {
                        const newActionRule = {
                          name: nameRef.current.value,
                          must_have_labels: mustHaveLabelsRef.current.value,
                          must_not_have_labels:
                            mustNotHaveLabelsRef.current.value,
                          action_id: actionRef.current.value,
                        };

                        setShowNameRequired(false);
                        setShowNameMustBeUnique(false);
                        setShowMustHaveLabelsRequired(false);
                        setShowActionRequired(false);

                        if (actionRuleIsValid(newActionRule, actionRules)) {
                          addActionRule(newActionRule);
                          resetForm();
                          setAdding(false);
                        } else {
                          setShowNameRequired(!newActionRule.name);
                          setShowNameMustBeUnique(
                            !actionRuleNameIsUnique(
                              nameRef.current.value,
                              actionRules,
                            ),
                          );
                          setShowMustHaveLabelsRequired(
                            !newActionRule.must_have_labels,
                          );
                          setShowActionRequired(
                            newActionRule.action_id === '0',
                          );
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
                        resetForm();
                        setShowNameRequired(false);
                        setShowNameMustBeUnique(false);
                        setShowMustHaveLabelsRequired(false);
                        setShowActionRequired(false);
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
                    nameRef={nameRef}
                    mustHaveLabelsRef={mustHaveLabelsRef}
                    mustNotHaveLabelsRef={mustNotHaveLabelsRef}
                    actionRef={actionRef}
                    showNameMustBeUnique={showNameMustBeUnique}
                  />
                </tr>
                {actionRulesTableRows}
              </tbody>
            </Table>
          </Col>
        </Row>
        <div className="feedback-toast-container">
          <Toast
            onClose={() => setShowDeletedActionRuleToast(false)}
            show={showDeletedActionRuleToast}
            delay={5000}
            autohide>
            <Toast.Body>The action rule was deleted.</Toast.Body>
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
    onSaveEditedActionRule,
  } = props;
  const [editing, setEditing] = useState(false);
  const [
    showDeleteActionRuleConfirmation,
    setShowDeleteActionRuleConfirmation,
  ] = useState(false);

  const [nameRef] = useState(React.createRef());
  const [mustHaveLabelsRef] = useState(React.createRef());
  const [mustNotHaveLabelsRef] = useState(React.createRef());
  const [actionRef] = useState(React.createRef());

  return (
    <>
      <tr hidden={editing}>
        <td>
          <Button
            className="mb-2 table-action-button"
            onClick={() => {
              nameRef.current.value = name;
              mustHaveLabelsRef.current.value = mustHaveLabels;
              mustNotHaveLabelsRef.current.value = mustNotHaveLabels;
              actionRef.current.value = actionId;
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
                <strong>{name}</strong>?
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
                Delete Action Rule
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
              const editedActionRule = {
                name: nameRef.current.value,
                must_have_labels: mustHaveLabelsRef.current.value,
                must_not_have_labels: mustNotHaveLabelsRef.current.value,
                action_id: actionRef.current.value,
              };
              onSaveEditedActionRule(name, editedActionRule);
              setEditing(false);
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
            onClick={() => setEditing(false)}>
            <ion-icon name="close" size="large" className="ion-icon-white" />
          </Button>
        </td>
        <ActionRuleFormColumns
          nameRef={nameRef}
          mustHaveLabelsRef={mustHaveLabelsRef}
          mustNotHaveLabelsRef={mustNotHaveLabelsRef}
          actionRef={actionRef}
        />
      </tr>
    </>
  );
}
