/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

/* eslint-disable react/prop-types */

import React, {useState} from 'react';
import Button from 'react-bootstrap/Button';
import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import Table from 'react-bootstrap/Table';

const actionRules = [
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
  const {nameRef, mustHaveLabelsRef, mustNotHaveLabelsRef, actionRef} = props;

  const actionOptions = actions.map(action => (
    <option key={action.id} value={action.id}>
      {action.name}
    </option>
  ));

  return (
    <>
      <td>
        <Form.Control type="text" required ref={nameRef} />
        <Form.Text>An action rule&rsquo;s name must be unique.</Form.Text>
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
  const [adding, setAdding] = useState(false);
  const [nameRef] = useState(React.createRef());
  const [mustHaveLabelsRef] = useState(React.createRef());
  const [mustNotHaveLabelsRef] = useState(React.createRef());
  const [actionRef] = useState(React.createRef());

  const actionRulesTableRows = actionRules.map(actionRule => (
    <ActionRulesTableRow
      key={actionRule.name}
      name={actionRule.name}
      mustHaveLabels={actionRule.must_have_labels}
      mustNotHaveLabels={actionRule.must_not_have_labels}
      actionId={actionRule.action_id}
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
                        const newActionRule = {
                          name: nameRef.current.value,
                          must_have_labels: mustHaveLabelsRef.current.value,
                          must_not_have_labels:
                            mustNotHaveLabelsRef.current.value,
                          action_id: actionRef.current.value,
                        };

                        actionRules.push(newActionRule);

                        actionRules.sort((a, b) =>
                          a.name.toLowerCase() > b.name.toLowerCase() ? 1 : -1,
                        );

                        setAdding(false);
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
                        nameRef.current.value = '';
                        mustHaveLabelsRef.current.value = '';
                        mustNotHaveLabelsRef.current.value = '';
                        actionRef.current.value = '0';
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
                  />
                </tr>
                {actionRulesTableRows}
              </tbody>
            </Table>
          </Col>
        </Row>
      </Container>
    </>
  );
}

function ActionRulesTableRow(props) {
  const {name, mustHaveLabels, mustNotHaveLabels, actionId} = props;
  const [editing, setEditing] = useState(false);
  const [deleted, setDeleted] = useState(false);
  const [nameRef] = useState(React.createRef());
  const [mustHaveLabelsRef] = useState(React.createRef());
  const [mustNotHaveLabelsRef] = useState(React.createRef());
  const [actionRef] = useState(React.createRef());

  return (
    <>
      <tr hidden={editing || deleted}>
        <td>
          <Button
            className="mb-2 table-action-button"
            onClick={() => setEditing(true)}>
            <ion-icon name="pencil" size="large" className="ion-icon-white" />
          </Button>{' '}
          <Button
            variant="secondary"
            className="table-action-button"
            onClick={() => setDeleted(true)}>
            <ion-icon
              name="trash-bin"
              size="large"
              className="ion-icon-white"
            />
          </Button>
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
      <tr hidden={!editing || deleted}>
        <td>
          <Button
            variant="outline-primary"
            className="mb-2 table-action-button"
            onClick={() => setEditing(false)}>
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
