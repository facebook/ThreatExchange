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
      <ActionPerformerSettings />
      <ActionLabelSettings />
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

function WebhookActioner({url, webhookType, headers}) {
  const actionerDetails = ActionerTypes.WebhookActioner;

  const [editing, setEditing] = useState(false);

  const [savedURL, setURL] = useState(url);
  const [savedWebhookType, setWebhookType] = useState(webhookType);
  const [savedHeaders, setHeaders] = useState(headers);
  const [tempURL, setTempURL] = useState(url);
  const [tempWebhookType, setTempWebhookType] = useState(webhookType);
  const [tempHeaders, setTempHeaders] = useState(headers);

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
          URL : {savedURL}
          <br />
          Webhook Type : {savedWebhookType}
          <br />
          Headers : {savedHeaders}
          <br />
        </Card.Body>
        <Card.Footer>
          <Button
            variant="primary"
            onClick={() => {
              setEditing(true);
            }}>
            Edit
          </Button>
        </Card.Footer>
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
                value={tempURL}
                onChange={e => {
                  setTempURL(e.target.value);
                }}
              />
              <Form.Label>Webhook Type</Form.Label>
              <Form.Text className="text-muted">
                {actionerDetails.args.webhookType.description}
              </Form.Text>
              <Form.Control
                as="select"
                value={tempWebhookType}
                onChange={e => {
                  setTempWebhookType(e.target.value);
                }}>
                <option>POST</option>
                <option>GET</option>
                <option>PUT</option>
                <option>DELETE</option>
              </Form.Control>

              <Form.Label>Headers</Form.Label>
              <Form.Text className="text-muted">
                {actionerDetails.args.headers.description}
              </Form.Text>
              <Form.Control
                type="text"
                value={tempHeaders}
                onChange={e => {
                  setTempHeaders(e.target.value);
                }}
              />
            </Form.Group>
          </Form>
        </Card.Body>
        <Card.Footer>
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
              setTempURL(savedURL);
              setTempWebhookType(savedWebhookType);
              setTempHeaders(savedHeaders);
              setEditing(false);
            }}>
            Cancel
          </Button>
        </Card.Footer>
      </div>
    </Card>
  );
}

const Actioners = {
  WebhookActioner,
};

function ActionPerformerRow({name, type, params}) {
  const [editing, setEditing] = useState(false);
  const [savedName, setName] = useState(name);
  const [tempName, setTempName] = useState(name);
  return (
    <tr key={name}>
      <td>
        <div hidden={editing}>
          {savedName}
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
            <Form.Group controlId="formName">
              <Form.Label>Action Name</Form.Label>
              <Form.Control
                type="text"
                placeholder="New Action Name"
                value={tempName}
                onChange={e => {
                  setTempName(e.target.value);
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
              setTempName(savedName);
              setEditing(false);
            }}>
            Cancel
          </Button>
        </div>
      </td>
      <td>{Actioners[type](params)}</td>
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
    <th key={header}>{header}</th>
  ));
  const performerBlocks = performers.map(performer =>
    ActionPerformerRow(performer),
  );
  return (
    <>
      <Card.Header>
        <h2 className="mt-2">Action Definitions</h2>
        <h5 className="mt-5">Define what to do for different Actions</h5>
      </Card.Header>
      <Card.Body>
        <Table striped bordered hover>
          <thead>
            <tr>{headerBlock}</tr>
          </thead>
          <tbody>{performerBlocks}</tbody>
        </Table>
      </Card.Body>
    </>
  );
}
