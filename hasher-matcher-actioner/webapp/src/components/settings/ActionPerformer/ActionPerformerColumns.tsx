/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState} from 'react';
import Form from 'react-bootstrap/Form';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import Tooltip from 'react-bootstrap/Tooltip';
import WebhookActioner from './WebhookActioner';
import {Action} from '../../../pages/settings/ActionSettingsTab';

export type WebhookActionPerformerParams = {
  url: string;
  headers: string;
};

const Actioners: ActionerMap = {
  WebhookPostActionPerformer: WebhookActioner,
  WebhookGetActionPerformer: WebhookActioner,
  WebhookDeleteActionPerformer: WebhookActioner,
  WebhookPutActionPerformer: WebhookActioner,
  '': WebhookActioner,
};

type ActionPerformerColumn = {
  action: Action;
  editing: boolean;
  updateAction: (action: Action) => void;
  canNotDeleteOrUpdateName: boolean;
};

interface ActionerMap {
  [key: string]: typeof WebhookActioner;
}

export default function ActionPerformerColumns({
  action,
  editing,
  updateAction,
  canNotDeleteOrUpdateName,
}: ActionPerformerColumn): JSX.Element {
  const [name, setName] = useState(action.name);

  return (
    <>
      <td>
        <div hidden={editing}>{action.name}</div>

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
                  value={action.name}
                  onChange={e => {
                    setName(e.target.value);
                    const newAction = action;
                    newAction.name = e.target.value;
                    updateAction(newAction);
                  }}
                />
              </Form.Group>
            )}
          </Form>
        </div>
      </td>
      <td>
        {Actioners[action.config_subtype]({
          action,
          editing,
          updateAction,
        })}
      </td>
    </>
  );
}
