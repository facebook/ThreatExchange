/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState} from 'react';
import Card from 'react-bootstrap/Card';
import Form from 'react-bootstrap/Form';
import {Action} from '../../../pages/settings/ActionSettingsTab';

interface WebhookTypeInterface extends Record<string, string> {
  WebhookPostActionPerformer: string;
  WebhookGetActionPerformer: string;
  WebhookDeleteActionPerformer: string;
  WebhookPutActionPerformer: string;
}

const ActionerTypes = {
  WebhookActioner: {
    args: {
      url: {description: 'The url to send a webhook to'},
      webhookType: {
        description: 'What type of webhook should be sent?',
        default: 'POST',
      },
      headers: {
        description: 'Optional json object of headers to include in webhook',
        default: '{}',
      },
    },
    description:
      'When a match occurs, a webhook will be sent to the specified url with data describing the match',
  },
};
const WebhookType: WebhookTypeInterface = {
  WebhookPostActionPerformer: 'POST',
  WebhookGetActionPerformer: 'GET',
  WebhookDeleteActionPerformer: 'DELETE',
  WebhookPutActionPerformer: 'PUT',
};
const actionerDetails = ActionerTypes.WebhookActioner;

type WebhookActioner = {
  action: Action;
  editing: boolean;
  updateAction: (action: Action) => void;
};

export default function WebhookActioner({
  action,
  editing,
  updateAction,
}: WebhookActioner): JSX.Element {
  const [url, setURL] = useState(action.params.url);
  const [headers, setHeaders] = useState(action.params.headers);
  const [webhookType, setWebhookType] = useState(action.config_subtype);

  return (
    <Card>
      <div hidden={editing}>
        <Card.Header>
          WebhookActioner
          <br />
          <Form.Text className="text-muted">
            {ActionerTypes.WebhookActioner.description}
          </Form.Text>
        </Card.Header>
        <Card.Body>
          URL : {url}
          <br />
          Webhook Type : {WebhookType[webhookType]}
          <br />
          Headers : {headers}
          <br />
        </Card.Body>
      </div>

      <div hidden={!editing}>
        <Card.Header>
          <Form>
            <Form.Group>
              <Form.Control as="select" size="lg">
                <option>WebhookActioner</option>
              </Form.Control>
            </Form.Group>
          </Form>
        </Card.Header>
        <Card.Body>
          <Form>
            <Form.Group>
              <Form.Label>URL</Form.Label>
              <Form.Text className="text-muted">
                {actionerDetails.args.url.description}
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
              <div>
                <Form.Label>Webhook Type</Form.Label>
                <Form.Text className="text-muted">
                  {actionerDetails.args.webhookType.description}
                </Form.Text>
                <Form.Control
                  as="select"
                  value={webhookType}
                  onChange={e => {
                    setWebhookType(e.target.value);
                    const newAction = action;
                    newAction.config_subtype = e.target.value;
                    updateAction(newAction);
                  }}>
                  <option value="">Please select one option</option>
                  <option value="WebhookPostActionPerformer">POST</option>
                  <option value="WebhookGetActionPerformer">GET</option>
                  <option value="WebhookPutActionPerformer">PUT</option>
                  <option value="WebhookDeleteActionPerformer">DELETE</option>
                </Form.Control>
              </div>
              <br />
              <Form.Label>Headers</Form.Label>
              <Form.Text className="text-muted">
                {actionerDetails.args.headers.description}
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
      </div>
    </Card>
  );
}
