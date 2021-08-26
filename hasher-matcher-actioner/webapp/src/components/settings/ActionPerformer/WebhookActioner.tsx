/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';
import Card from 'react-bootstrap/Card';
import Form from 'react-bootstrap/Form';
import PropTypes from 'prop-types';

interface WebhookTypeInterface extends Record<string, any> {
  WebhookPostActionPerformer: string;
  WebhookGetActionPerformer: string;
  WebhookDeleteActionPerformer: string;
  WebhookPutActionPerformer: string;
}

type WebhookActioner = {
  url: string;
  headers: string;
  webhookType: string;
  editing: boolean;
  onChange: (key: string, keyValueMap: {[key: string]: string}) => void;
};

export default function WebhookActioner({
  url,
  headers,
  webhookType,
  editing,
  onChange,
}: WebhookActioner): JSX.Element {
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
                  onChange('url', {url: e.target.value});
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
                    onChange('config_subtype', {
                      config_subtype: e.target.value,
                    });
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
                  onChange('headers', {headers: e.target.value});
                }}
              />
            </Form.Group>
          </Form>
        </Card.Body>
      </div>
    </Card>
  );
}

WebhookActioner.propTypes = {
  url: PropTypes.string.isRequired,
  headers: PropTypes.string.isRequired,
  editing: PropTypes.bool.isRequired,
  webhookType: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
};
