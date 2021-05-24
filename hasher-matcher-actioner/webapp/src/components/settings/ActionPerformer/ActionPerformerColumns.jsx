/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';
import Form from 'react-bootstrap/Form';
import {PropTypes} from 'prop-types';
import WebhookActioner from './WebhookActioner';

export default function ActionPerformerColumns({
  name,
  type,
  params,
  editing,
  onChange,
}) {
  const Actioners = {
    WebhookPostActionPerformer: WebhookActioner,
    WebhookGetActionPerformer: WebhookActioner,
    WebhookDeleteActionPerformer: WebhookActioner,
    WebhookPutActionPerformer: WebhookActioner,
    '': WebhookActioner,
  };
  return (
    <>
      <td>
        <div hidden={editing}>{name}</div>

        <div hidden={!editing}>
          <Form>
            <Form.Group>
              <Form.Label>Action Name</Form.Label>
              <Form.Control
                type="text"
                placeholder="New Action Name"
                value={name}
                onChange={e => {
                  onChange('name', {name: e.target.value});
                }}
              />
            </Form.Group>
          </Form>
        </div>
      </td>
      <td>
        {Actioners[type]({
          webhookType: type,
          editing,
          ...params,
          onChange,
        })}
      </td>
    </>
  );
}

ActionPerformerColumns.propTypes = {
  name: PropTypes.string.isRequired,
  type: PropTypes.string.isRequired,
  editing: PropTypes.bool.isRequired,
  params: PropTypes.shape({
    url: PropTypes.string.isRequired,
    headers: PropTypes.string.isRequired,
  }).isRequired,
  onChange: PropTypes.func.isRequired,
};
