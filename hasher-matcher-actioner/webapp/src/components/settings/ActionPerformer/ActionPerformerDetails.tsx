/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React, {useState} from 'react';
import {InputGroup, Col, Button, Form, Card} from 'react-bootstrap';
import {ActionPerformer} from '../../../pages/settings/ActionPerformerSettingsTab';
import {ActionPerformerType} from '../../../utils/constants';

const actionPerformerDetails = {
  params: {
    url: {description: 'The url to send a webhook to'},
    headers: {
      description: 'Optional json object of headers to include in webhook',
      default: '{}',
    },
    extension_name: {
      description:
        'The name for the extension implementations whose mapping defined in settings.py',
    },
    additional_kwargs: {
      description: 'keyword mapping passed to the implementations.',
    },
  },
  config_subtype: {
    description:
      'The kind of action performer to use: Webhook types sends a web request. Custom Implementation run code added to hmalib_extentions',
  },
};

type ActionPerformerDetails = {
  action: ActionPerformer;
  editing: boolean;
  updateAction: (action: ActionPerformer) => void;
};

type kwargs = {[key: string]: {key: string; value: string}};

const packageKWArgs = (kwargs: kwargs): Record<string, string> => {
  const entries: Record<string, string> = {};
  Object.values(kwargs).forEach((entry: {key: string; value: string}) => {
    entries[entry.key] = entry.value;
  });
  return entries;
};

const unPackageKWArgs = (kwargs: Record<string, string>): kwargs => {
  const result: kwargs = {};
  Object.entries(kwargs).forEach(([key, value], index) => {
    result[String(index)] = {key, value};
  });
  return result;
};

export default function ActionPerformerDetails({
  action,
  editing,
  updateAction,
}: ActionPerformerDetails): JSX.Element {
  const [actionerType, setActionerType] = useState(action.config_subtype);
  const [url, setURL] = useState(action.params.url);
  const [headers, setHeaders] = useState(action.params.headers);
  const [extensionName, setExtensionName] = useState(
    action.params.extension_name,
  );
  const [kwargs, setKWArgs] = useState<kwargs>(
    unPackageKWArgs(action.params.additional_kwargs ?? {}),
  );

  const WebHookActionerBody = (): JSX.Element => (
    <>
      <Card.Body hidden={editing}>
        URL : {url}
        <br />
        Headers : {headers}
        <br />
      </Card.Body>
      <Card.Body hidden={!editing}>
        <Form>
          <Form.Group>
            <Form.Label>URL</Form.Label>
            <Form.Text className="text-muted">
              {actionPerformerDetails.params.url.description}
            </Form.Text>
            <Form.Control
              type="url"
              value={url}
              onChange={e => {
                setURL(e.target.value);
                const newAction = action;
                newAction.params.url = e.target.value;
                updateAction(newAction);
              }}
            />
            <br />
            <Form.Label>Headers</Form.Label>
            <Form.Text className="text-muted">
              {actionPerformerDetails.params.headers.description}
            </Form.Text>
            <Form.Control
              type="text"
              value={headers}
              onChange={e => {
                setHeaders(e.target.value);
                const newAction = action;
                newAction.params.headers = e.target.value;
                updateAction(newAction);
              }}
            />
          </Form.Group>
        </Form>
      </Card.Body>
    </>
  );

  const kwargsField = (): JSX.Element => (
    <Form>
      <Form.Group>
        <Form.Label>
          Keyword Args: {Object.keys(kwargs).length > 0 ? '' : 'None'}
        </Form.Label>
        <Form.Text hidden={!editing} className="text-muted">
          {actionPerformerDetails.params.additional_kwargs.description}
        </Form.Text>

        {Object.keys(kwargs).map(entry => (
          <Form.Row key={entry}>
            <Form.Group as={Col}>
              <InputGroup>
                <Form.Control
                  disabled={!editing}
                  value={kwargs[entry].key}
                  onChange={e => {
                    const copy = {...kwargs};
                    copy[entry].key = e.target.value;
                    setKWArgs(copy);
                    const newAction = action;
                    newAction.params.additional_kwargs = packageKWArgs(kwargs);
                    updateAction(newAction);
                  }}
                />
              </InputGroup>
            </Form.Group>
            :
            <Form.Group as={Col}>
              <InputGroup>
                <Form.Control
                  disabled={!editing}
                  value={kwargs[entry].value}
                  onChange={(e: React.FormEvent) => {
                    const target = e.target as typeof e.target & {
                      value: string;
                    };
                    const copy = {...kwargs};
                    copy[entry].value = target.value;
                    setKWArgs(copy);
                    const newAction = action;
                    newAction.params.additional_kwargs = packageKWArgs(kwargs);
                    updateAction(newAction);
                  }}
                />
              </InputGroup>
            </Form.Group>
            <Form.Group>
              <Button
                hidden={!editing}
                variant="danger"
                className="float-right"
                onClick={() => {
                  const copy = {...kwargs};
                  delete copy[entry];
                  setKWArgs(copy);
                }}>
                -
              </Button>
            </Form.Group>
          </Form.Row>
        ))}
        <Form.Group>
          <Button
            hidden={!editing}
            variant="success"
            onClick={() => {
              setKWArgs({
                ...kwargs,
                [Object.keys(kwargs).length]: {},
              });
            }}>
            +
          </Button>
        </Form.Group>
      </Form.Group>
    </Form>
  );

  const CustomActionerBody = (): JSX.Element => (
    <>
      <Card.Body hidden={editing}>
        <Form.Label> Extension Name: {extensionName}</Form.Label>
        <br />
        {kwargsField()}
      </Card.Body>

      <Card.Body hidden={!editing}>
        <Form>
          <Form.Group>
            <Form.Label>Extension Name</Form.Label>
            <Form.Text className="text-muted">
              {actionPerformerDetails.params.extension_name.description}
            </Form.Text>
            <Form.Control
              type="text"
              value={extensionName}
              onChange={e => {
                setExtensionName(e.target.value);
                const newAction = action;
                newAction.params.extension_name = e.target.value;
                updateAction(newAction);
              }}
            />
          </Form.Group>
        </Form>
        <br />
        {kwargsField()}
      </Card.Body>
    </>
  );

  return (
    <Card>
      <Card.Header>
        <Form>
          <Form.Group>
            <Form.Label>Action Type</Form.Label>
            <Form.Control
              as="select"
              disabled={!editing}
              value={actionerType}
              onChange={e => {
                setActionerType(e.target.value);
                const newAction = action;
                newAction.config_subtype = e.target.value;
                updateAction(newAction);
              }}>
              <option value="">Please select one option</option>
              <option value={ActionPerformerType.WebhookPostActionPerformer}>
                POST Webhook
              </option>
              <option value={ActionPerformerType.WebhookGetActionPerformer}>
                GET Webhook
              </option>
              <option value={ActionPerformerType.WebhookPutActionPerformer}>
                PUT Webhook
              </option>
              <option value={ActionPerformerType.WebhookDeleteActionPerformer}>
                DELETE Webhook
              </option>
              <option value={ActionPerformerType.CustomImplActionPerformer}>
                Custom Implementation
              </option>
            </Form.Control>
            <Form.Text hidden={!editing} className="text-muted">
              {actionPerformerDetails.config_subtype.description}
            </Form.Text>
          </Form.Group>
        </Form>
      </Card.Header>
      {actionerType === 'CustomImplActionPerformer'
        ? CustomActionerBody()
        : WebHookActionerBody()}
    </Card>
  );
}
