/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';
import {PropTypes} from 'prop-types';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';

const classificationOptions = [
  <option key="Dataset Source" value="BankSourceClassification">
    Dataset Source
  </option>,
  <option key="Dataset ID" value="BankIDClassification">
    Dataset ID
  </option>,
  <option key="MatchedContent ID" value="BankedContentIDClassification">
    MatchedContent ID
  </option>,
  <option key="MatchedContent Classification" value="Classification">
    MatchedContent Classification
  </option>,
];
export default function ActionRuleFormColumns({
  actions,
  name,
  classifications,
  actionId,
  showErrors,
  nameIsUnique,
  oldName,
  onChange,
}) {
  const renderClassificationRow = (
    classification,
    onClassificationChange,
    index,
  ) => (
    <Row key={index}>
      <Col key="select-classification-type">
        <Form.Control
          as="select"
          required
          value={classification.classification_type}
          onChange={e => {
            const newClassification = classification;
            newClassification.classification_type = e.target.value;
            onClassificationChange(newClassification);
          }}>
          {classificationOptions}
        </Form.Control>
      </Col>
      <Col xs="auto" key="select-classification-equals">
        <Form.Control
          as="select"
          required
          value={classification.equals}
          onChange={e => {
            const newClassification = classification;
            newClassification.equals = e.target.value === 'true';
            onClassificationChange(newClassification);
          }}>
          <option key="Equal" value="true">
            =
          </option>
          <option key="NotEqual" value="false">
            ≠
          </option>
        </Form.Control>
      </Col>
      <Col key="select-classification-value">
        <Form.Control
          type="text"
          value={classification.classification_value}
          required
          onChange={e => {
            const newClassification = classification;
            newClassification.classification_value = e.target.value;
            onClassificationChange(newClassification);
          }}
          selected
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
        <Form>
          <Form.Label>
            Classifications
            <span hidden={!showErrors || classifications.length === 0}>
              {' '}
              (required)
            </span>
          </Form.Label>
          {classifications
            ? classifications.map((classification, index) => {
                const onClassificationChange = newClassification => {
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
        </Form>
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
