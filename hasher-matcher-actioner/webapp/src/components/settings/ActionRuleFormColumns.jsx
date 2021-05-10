/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';
import {PropTypes} from 'prop-types';
import Form from 'react-bootstrap/Form';

export default function ActionRuleFormColumns({
  actions,
  name,
  mustHaveLabels,
  mustNotHaveLabels,
  actionId,
  showErrors,
  nameIsUnique,
  oldName,
  onChange,
}) {
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
  mustHaveLabels: PropTypes.string.isRequired,
  mustNotHaveLabels: PropTypes.string.isRequired,
  actionId: PropTypes.string.isRequired,
  showErrors: PropTypes.bool.isRequired,
  nameIsUnique: PropTypes.func.isRequired,
  oldName: PropTypes.string,
  onChange: PropTypes.func.isRequired,
};

ActionRuleFormColumns.defaultProps = {
  oldName: undefined,
};
