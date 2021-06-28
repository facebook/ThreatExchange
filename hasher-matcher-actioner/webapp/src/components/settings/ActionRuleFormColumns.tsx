/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Button from 'react-bootstrap/Button';

export const classificationTypeTBD = 'TBD';

type Action = {
  id: string;
  name: string;
};

type ClassificationCondition = {
  classificationType: string;
  classificationValue: string;
  equalTo: boolean;
};

type Input = {
  actions: Action[];
  name: string;
  classifications: ClassificationCondition[];
  actionId: string;
  showErrors: boolean;
  nameIsUnique: (newName: string, oldName: string) => boolean;
  oldName: string;
  onChange: (updatedField: Record<string, unknown>) => void;
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
          isInvalid={showErrors && classifications.every(clsf => !clsf.equalTo)}
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
          An ActionRule&rsquo;s name must be unique.
        </Form.Text>
      </td>
      <td>
        <Form.Label>
          Classifications{' '}
          <span
            hidden={
              !showErrors ||
              (!!classifications.length &&
                classifications.some(classification => classification.equalTo))
            }>
            (at least one &ldquo;equals&rdquo; Classification required)
          </span>
        </Form.Label>
        {classifications
          ? classifications.map((classification, index) => {
              const onClassificationChange = (
                newClassification: ClassificationCondition,
              ) => {
                const newClassifications = classifications;
                newClassifications[index] = newClassification;
                onChange({classifications: newClassifications});
              };
              const onClassificationDelete = () => {
                const newClassifications = classifications;
                newClassifications.splice(index, 1);
                onChange({classifications: newClassifications});
              };
              return renderClassificationRow(
                classification,
                index,
                onClassificationChange,
                onClassificationDelete,
              );
            })
          : []}
        <br />
        <Button
          variant="success"
          onClick={() => {
            const newClassifications = classifications;
            newClassifications.push({
              classificationType: classificationTypeTBD,
              equalTo: true,
              classificationValue: '',
            });
            onChange({classifications: newClassifications});
          }}>
          +
        </Button>
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
            Select ...
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
      classificationType: PropTypes.string.isRequired,
      equalTo: PropTypes.bool.isRequired,
      classificationValue: PropTypes.string.isRequired,
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
