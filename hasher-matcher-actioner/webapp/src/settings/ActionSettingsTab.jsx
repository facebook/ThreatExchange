/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

/* eslint-disable react/prop-types */

import React, {useState} from 'react';
import Card from 'react-bootstrap/Card';
import Button from 'react-bootstrap/Button';
import Table from 'react-bootstrap/Table';
import Form from 'react-bootstrap/Form';

export default function ActionSettingsTab() {
  return (
    <>
      <ActionLabelSettings />
      <ActionPerformerSettings />
    </>
  );
}

function ActionLabelSettings() {
  return <>Action Label Settings coming here</>;
}

const ActionerTypes = {
  WebhookActioner: {
    args: {
      url: {description: 'The url to send a webhook to'},
      webhookType: {
        description:
          'What type of webhook should be sent (POST, DELETE, PUT, or GET)',
        default: 'POST',
      },
      headers: {
        description: 'Optional json object of headers to include in webhook',
        default: '{}',
      },
    },
    description:
      'When configured for a match, the WebhookActioner will send a webhook to the specified url with data describing the match',
  },
};

function WebhookActionerRender({url, webhookType, headers}) {
  const actionerDetails = ActionerTypes.WebhookActioner;

  const [editing, setEditing] = useState(false);
  const [newURL, setURL] = useState(url);
  const [newWebhookType, setWebhookType] = useState(webhookType);
  const [newHeaders, setHeaders] = useState(headers);

  let tempURL = newURL;
  let tempWebhookType = newWebhookType;
  let tempHeaders = newHeaders;
  return (
    <Card>
      <div hidden={editing}>
        <h5>WebhookActionerRender</h5>
        URL : {newURL}
        <br />
        Webhook Type : {newWebhookType}
        <br />
        Headers : {newHeaders}
        <br />
        <Button
          variant="primary"
          onClick={() => {
            setEditing(true);
          }}>
          Edit
        </Button>
      </div>

      <div hidden={!editing}>
        <Form>
          <Form.Group>
            <Form.Label>Action Type</Form.Label>
            <Form.Control as="select" size="lg">
              <option>WebhookActioner</option>
            </Form.Control>

            <Form.Label>URL</Form.Label>
            <Form.Control
              type="url"
              placeholder={actionerDetails.args.url.description}
              onChange={e => {
                tempURL = e.target.value;
              }}
            />

            <Form.Label>Webhook Type</Form.Label>
            <Form.Control
              as="select"
              placeholder={actionerDetails.args.webhookType.description}
              onChange={e => {
                tempWebhookType = e.target.value;
              }}>
              <option>POST</option>
              <option>GET</option>
              <option>PUT</option>
              <option>DELETE</option>
            </Form.Control>

            <Form.Label>Headers</Form.Label>
            <Form.Control
              type="text"
              placeholder={actionerDetails.args.headers.description}
              onChange={e => {
                tempHeaders = e.target.value;
              }}
            />
          </Form.Group>
        </Form>
        <Button
          variant="primary"
          onClick={() => {
            setURL(tempURL);
            setWebhookType(tempWebhookType);
            setHeaders(tempHeaders);
            setEditing(false);
          }}>
          Save
        </Button>
        <Button
          variant="danger"
          onClick={() => {
            setEditing(false);
          }}>
          Cancel
        </Button>
      </div>
    </Card>
  );
}

const ActionRenderers = {
  WebhookActioner: WebhookActionerRender,
};

function ActionPerformerRow({name, type, params}) {
  const [editing, setEditing] = useState(false);
  const [newName, setName] = useState(name);
  let tempName = name;
  return (
    <tr>
      <td>
        <div hidden={editing}>
          {' '}
          {newName}
          <Button
            variant="primary"
            onClick={() => {
              setEditing(true);
            }}>
            Edit
          </Button>
        </div>

        <div hidden={!editing}>
          <Form>
            <Form.Group controlId="formName">
              <Form.Label>Action Name</Form.Label>
              <Form.Control
                type="text"
                placeholder="New Action Name"
                onChange={e => {
                  tempName = e.target.value;
                }}
              />
            </Form.Group>
          </Form>

          <Button
            variant="primary"
            onClick={() => {
              setName(tempName);
              setEditing(false);
            }}>
            Save
          </Button>
          <Button
            variant="danger"
            onClick={() => {
              setEditing(false);
            }}>
            Cancel
          </Button>
        </div>
      </td>
      <td>{ActionRenderers[type](params)}</td>
    </tr>
  );
}

function ActionPerformerSettings() {
  const initPerformers = [
    {
      name: 'MyFirstAction',
      type: 'WebhookActioner',
      params: {
        url: 'myurl.com',
        webhookType: 'POST',
        headers: '{"h1" : "header"}',
      },
      editing: {
        name: false,
        details: false,
      },
    },
    {
      name: 'MySecondAction',
      type: 'WebhookActioner',
      params: {
        url: 'myotherurl.com',
        webhookType: 'DELETE',
        headers: '{"h4" : "header"}',
      },
      editing: {
        name: false,
        details: false,
      },
    },
  ];
  const [performers] = useState(initPerformers);
  // const [editing, setEditing] = useState([false, false]);

  const headerBlock = ['Action Name', 'Action Details'].map(header => (
    <th>{header}</th>
  ));
  const performerBlocks = performers.map(performer =>
    ActionPerformerRow(performer),
  );
  return (
    <>
      <h2 className="mt-4">Action Definitions</h2>
      <h5 className="mt-5">Define what the Actions above mean</h5>
      <Table striped bordered hover>
        <thead>
          <tr>{headerBlock}</tr>
        </thead>
        <tbody>{performerBlocks}</tbody>
      </Table>
    </>
  );
}
