/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';

type Action = {
  id: string;
  name: string;
};

type Classification = {
  classification_type: string;
  equals: boolean;
  classification_value: string;
};

type Input = {
  actions: Action[];
  name: string;
  classifications: Classification[];
  actionId: string;
  showErrors: boolean;
  nameIsUnique: (newName: string, oldName: string) => boolean;
  oldName: string;
  onChange: (updatedField: Object) => void;
};

export default function ActionRuleFormColumns({
  actions,
  name,
  classifications,
  actionId,
  showErrors,
  nameIsUnique,
  oldName,
  onChange,
}: Input) {
  const renderClassificationRow = (
    classification: Classification,
    onClassificationChange: (new_classification: Classification) => void,
    index: number,
  ) => (
    <Row key={index} style={{marginBottom: 3, marginLeft: 3}}>
      <Col>
        <Form.Control
          as="select"
          required
          value={classification.classification_type}
          onChange={e => {
            const newClassification = classification;
            newClassification.classification_type = e.target.value;
            onClassificationChange(newClassification);
          }}>
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
          value={classification.equals ? 'true' : 'false'}
          onChange={e => {
            const newClassification = classification;
            newClassification.equals = e.target.value === 'true';
            onClassificationChange(newClassification);
          }}>
          <option value="true">=</option>
          <option value="false">≠</option>
        </Form.Control>
      </Col>
      <Col>
        <Form.Control
          type="text"
          value={classification.classification_value}
          required
          onChange={e => {
            const newClassification = classification;
            newClassification.classification_value = e.target.value;
            onClassificationChange(newClassification);
          }}
          // selected
          isInvalid={showErrors && !classification.classification_value}
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
          <span hidden={!showErrors || !!name}> (required)</span>
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
          Classifications
          <span hidden={!showErrors || !!classifications.length}>
            {' '}
            (required)
          </span>
        </Form.Label>
        {classifications
          ? classifications.map((classification, index) => {
              const onClassificationChange = (
                newClassification: Classification,
              ) => {
                const newClassifications = classifications;
                newClassifications[index] = newClassification;
                onChange({classifications: newClassifications});
              };
              return renderClassificationRow(
                classification,
                onClassificationChange,
                index,
              );
            })
          : []}
      </td>
      <td>
        <Form.Label>
          Action
          <span hidden={!showErrors || actionId !== '0'}> (required)</span>
        </Form.Label>
        <Form.Control
          as="select"
          required
          value={actionId}
          onChange={e => onChange({action_id: e.target.value})}
          isInvalid={showErrors && actionId === '0'}>
          <option value="0" key="0">
            Select an action...
          </option>
          {actionOptions}
        </Form.Control>
      </td>
    </>
  );
}

ActionRuleFormColumns.propTypes = {
  actions: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
    }),
  ).isRequired,
  name: PropTypes.string.isRequired,
  classifications: PropTypes.arrayOf(
    PropTypes.shape({
      classification_type: PropTypes.string.isRequired,
      equals: PropTypes.bool.isRequired,
      classification_value: PropTypes.string.isRequired,
    }),
  ),
  actionId: PropTypes.string.isRequired,
  showErrors: PropTypes.bool.isRequired,
  nameIsUnique: PropTypes.func.isRequired,
  oldName: PropTypes.string,
  onChange: PropTypes.func.isRequired,
};

ActionRuleFormColumns.defaultProps = {
  oldName: undefined,
  classifications: [],
};
