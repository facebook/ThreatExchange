/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Button from 'react-bootstrap/Button';
import type {
  Action,
  ActionRule,
  ClassificationCondition,
} from '../../pages/settings/ActionRuleSettingsTab';

export const classificationTypeTBD = 'TBD';

type Input = {
  actions: Action[];
  actionRule: ActionRule;
  showErrors: boolean;
  nameIsUnique: (newName: string, oldName: string) => boolean;
  oldName: string;
  onChange: (field_name: string, new_value: any) => void;
};

export default function ActionRuleFormColumns({
  actions,
  actionRule,
  showErrors,
  nameIsUnique,
  oldName,
  onChange,
}: Input): JSX.Element {
  const renderClassificationRow = (
    classification: ClassificationCondition,
    index: number,
    onClassificationChange: (
      newClassification: ClassificationCondition,
    ) => void,
    onClassificationDelete: () => void,
  ) => (
    <Row key={index} style={{marginBottom: 3}}>
      <Col xs={1}>
        <Button variant="danger" onClick={onClassificationDelete}>
          -
        </Button>
      </Col>
      <Col>
        <Form.Control
          as="select"
          required
          value={classification.classificationType}
          onChange={e => {
            const newClassification = classification;
            newClassification.classificationType = e.target.value;
            onClassificationChange(newClassification);
          }}
          isInvalid={
            showErrors &&
            classification.classificationType === classificationTypeTBD
          }>
          <option value={classificationTypeTBD}> Select... </option>
          <option value="BankSourceClassification">Dataset Source</option>
          <option value="BankIDClassification">Dataset ID</option>
          <option value="BankedContentIDClassification">
            MatchedSignal ID
          </option>
          <option value="Classification">MatchedSignal</option>
        </Form.Control>
      </Col>
      <Col xs={2}>
        <Form.Control
          as="select"
          required
          value={classification.equalTo ? 'Equals' : 'Not Equals'}
          isInvalid={
            showErrors &&
            actionRule.classification_conditions.every(clsf => !clsf.equalTo)
          }
          onChange={e => {
            const newClassification = classification;
            newClassification.equalTo = e.target.value === 'Equals';
            onClassificationChange(newClassification);
          }}>
          <option value="Equals">=</option>
          <option value="Not Equals">≠</option>
        </Form.Control>
      </Col>
      <Col>
        <Form.Control
          type="text"
          value={classification.classificationValue}
          required
          onChange={e => {
            const newClassification = classification;
            newClassification.classificationValue = e.target.value;
            onClassificationChange(newClassification);
          }}
          // selected
          isInvalid={showErrors && !classification.classificationValue}
        />
      </Col>
    </Row>
  );

  const actionOptions = actions
    ? actions.map(action => (
        <option key={action.id} value={action.id}>
          {action.name}
        </option>
      ))
    : [];

  return (
    <>
      <td>
        <Form.Label>
          Name
          <span hidden={!showErrors || !!actionRule.name}> (required)</span>
        </Form.Label>
        <Form.Control
          type="text"
          required
          value={actionRule.name}
          onChange={e => onChange('name', e.target.value)}
          isInvalid={showErrors && !actionRule.name}
        />
        <Form.Text
          hidden={!showErrors || nameIsUnique(actionRule.name, oldName)}
          className="text-danger">
          An ActionRule&rsquo;s name must be unique.
        </Form.Text>
      </td>
      <td>
        <Form.Label>
          Classifications{' '}
          <span
            hidden={
              !showErrors ||
              (!!actionRule.classification_conditions.length &&
                actionRule.classification_conditions.some(
                  classification => classification.equalTo,
                ))
            }>
            (at least one &ldquo;equals&rdquo; Classification required)
          </span>
        </Form.Label>
        {actionRule.classification_conditions
          ? actionRule.classification_conditions.map(
              (classification, index) => {
                const onClassificationChange = (
                  newClassification: ClassificationCondition,
                ) => {
                  const newClassifications =
                    actionRule.classification_conditions;
                  newClassifications[index] = newClassification;
                  onChange('classification_conditions', newClassifications);
                };
                const onClassificationDelete = () => {
                  const newClassifications =
                    actionRule.classification_conditions;
                  newClassifications.splice(index, 1);
                  onChange('classification_conditions', newClassifications);
                };
                return renderClassificationRow(
                  classification,
                  index,
                  onClassificationChange,
                  onClassificationDelete,
                );
              },
            )
          : []}
        <br />
        <Button
          variant="success"
          onClick={() => {
            const newClassifications = actionRule.classification_conditions;
            newClassifications.push({
              classificationType: classificationTypeTBD,
              equalTo: true,
              classificationValue: '',
            });
            onChange('classification_conditions', newClassifications);
          }}>
          +
        </Button>
      </td>
      <td>
        <Form.Label>
          Action
          <span hidden={!showErrors || actionRule.action_id !== '0'}>
            {' '}
            (required)
          </span>
        </Form.Label>
        <Form.Control
          as="select"
          required
          value={actionRule.action_id}
          onChange={e => onChange('action_id', e.target.value)}
          isInvalid={showErrors && actionRule.action_id === '0'}>
          <option value="0" key="0">
            Select ...
          </option>
          {actionOptions}
        </Form.Control>
      </td>
    </>
  );
}
