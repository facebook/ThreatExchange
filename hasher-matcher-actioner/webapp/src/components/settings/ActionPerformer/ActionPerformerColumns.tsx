/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';
import Form from 'react-bootstrap/Form';
import PropTypes from 'prop-types';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import Tooltip from 'react-bootstrap/Tooltip';
import WebhookActioner from './WebhookActioner';

export type WebhookActionPerformerParams = {
  url: string;
  headers: string;
};

type ActionPerformerColumn = {
  name: string;
  type: string;
  params: WebhookActionPerformerParams;
  editing: boolean;
  onChange: (key: string, keyValueMap: {[key: string]: string}) => void;
  canNotDeleteOrUpdateName: boolean;
};

interface ActionerMap {
  [key: string]: typeof WebhookActioner;
}

export default function ActionPerformerColumns({
  name,
  type,
  params,
  editing,
  onChange,
  canNotDeleteOrUpdateName,
}: ActionPerformerColumn): JSX.Element {
  const Actioners: ActionerMap = {
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
            {canNotDeleteOrUpdateName ? (
              <OverlayTrigger
                overlay={
                  <Tooltip id={`tooltip-disabled-${name}`}>
                    The action {name}&apos;s name can not be modified because it
                    is currently being used by one or more action rules. Please
                    edit the rule(s) to refer to another action, or delete the
                    rule(s), then retry.
                  </Tooltip>
                }>
                <Form.Label>{name}</Form.Label>
              </OverlayTrigger>
            ) : (
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
            )}
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
  canNotDeleteOrUpdateName: PropTypes.bool.isRequired,
};
