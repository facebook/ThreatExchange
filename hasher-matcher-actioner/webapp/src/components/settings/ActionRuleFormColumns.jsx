/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

/* eslint-disable react/prop-types */

import React from 'react';
import Form from 'react-bootstrap/Form';

export default function ActionRuleFormColumns({
  actions,
  name,
  mustHaveLabels,
  mustNotHaveLabels,
  action,
  showErrors,
  nameIsUnique,
  oldName,
  onChange,
}) {
  const actionOptions = actions
    ? actions.map(actn => (
        <option key={actn.id} value={actn.id}>
          {actn.name}
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
