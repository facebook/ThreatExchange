/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';
import {PropTypes} from 'prop-types';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';

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
  // const classifications = [
  //   {
  //     classification_type: 'BankSourceClassification',
  //     equals: true,
  //     classification_value: mustHaveLabels + mustNotHaveLabels,
  //   },
  // ];

  const classificationOptions = [
    <option key="Dataset Source" value="BankSourceClassification">
      Dataset Source
    </option>,
    <option key="Dataset ID" value="BankIDClassification">
      Dataset ID
    </option>,
    <option key="Matched Content ID" value="BankedContentIDClassification">
      Matched Content ID
    </option>,
    <option key="Matched Content Tag" value="Classification">
      Matched Content Tag
    </option>,
  ];

  const classificationOptionValues = {
    BankSourceClassification: {
      form_type: 'select',
      options: [
        <option key="te" value="te">
          ThreatExchange
        </option>,
      ],
    },
    BankIDClassification: {
      form_type: 'select',
      options: [
        <option key="1" value="1">
          DS 1
        </option>,
        <option key="2" value="2">
          DS 2
        </option>,
      ],
    },
    BankedContentIDClassification: {
      form_type: 'text',
    },
    Classification: {
      form_type: 'select',
      options: [
        <option key="1a" value="1">
          Tag 1
        </option>,
        <option key="2a" value="2">
          DS 2
        </option>,
      ],
    },
  };

  const renderClassificationRow = (classification, index) => {
    const onClassificationChange = newClassification => {
      const newClassifications = classifications;
      newClassifications[index] = newClassification;
      onChange({must_have_labels: newClassifications});
    };

    return (
      <Row key={index}>
        <Col key="select-classification-type">
          <Form.Control
            as="select"
            required
            onChange={e => {
              const newClassification = classification;
              newClassification.classification_type = e.target.value;
              onClassificationChange(newClassification);
            }}
            isInvalid={showErrors && classifications.length > 0}>
            {classificationOptions}
          </Form.Control>
        </Col>
        <Col xs="auto" key="select-classification-equals">
          <Form.Control
            as="select"
            required
            onChange={e => {
              const newClassification = classification;
              newClassification.equals = e.target.value;
              onClassificationChange(newClassification);
            }}>
            <option key="Equal" value>
              =
            </option>
            <option key="NotEqual" value={false}>
              ≠
            </option>
          </Form.Control>
        </Col>
        <Col key="select-classification-value">
          <Form.Control
            // as={
            //   classificationOptionValues[
            //     classifications[0].classification_type
            //   ].form_type
            // }
            as="select"
            required
            onChange={e => {
              const newClassification = classification;
              newClassification.classification_value = e.target.value;
              onClassificationChange(newClassification);
            }}>
            {
              classificationOptionValues[classifications[0].classification_type]
                .options
            }
          </Form.Control>
        </Col>
      </Row>
    );
  };

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
            ? classifications.map((classification, index) =>
                renderClassificationRow(classification, index),
              )
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
  ).isRequired,
  actionId: PropTypes.string.isRequired,
  showErrors: PropTypes.bool.isRequired,
  nameIsUnique: PropTypes.func.isRequired,
  oldName: PropTypes.string,
  onChange: PropTypes.func.isRequired,
};

ActionRuleFormColumns.defaultProps = {
  oldName: undefined,
};
