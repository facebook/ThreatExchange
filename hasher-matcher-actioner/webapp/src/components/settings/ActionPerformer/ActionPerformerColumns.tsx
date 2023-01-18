/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React, {useState} from 'react';
import Form from 'react-bootstrap/Form';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import Tooltip from 'react-bootstrap/Tooltip';
import ActionPerfomerDetails from './ActionPerformerDetails';
import {ActionPerformer} from '../../../pages/settings/ActionPerformerSettingsTab';

type ActionPerformerColumn = {
  action: ActionPerformer;
  editing: boolean;
  updateAction: (action: ActionPerformer) => void;
  canNotDeleteOrUpdateName: boolean;
};

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
        <div hidden={editing}>
          {canNotDeleteOrUpdateName ? (
            <OverlayTrigger
              overlay={
                <Tooltip id={`tooltip-disabled-${name}`}>
                  This action cannot be deleted nor can the name be modified
                  because it is currently being used by one or more action
                  rules.
                </Tooltip>
              }>
              <Form.Label>{name}</Form.Label>
            </OverlayTrigger>
          ) : (
            action.name
          )}
        </div>

        <div hidden={!editing}>
          <Form>
            {canNotDeleteOrUpdateName ? (
              <OverlayTrigger
                overlay={
                  <Tooltip id={`tooltip-disabled-${name}`}>
                    This action name cannot be modified because it is currently
                    being used by one or more action rules. Please edit the
                    rule(s) to refer to another action, or delete the rule(s),
                    then retry.
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
        {ActionPerfomerDetails({
          action,
          editing,
          updateAction,
        })}
      </td>
    </>
  );
}
