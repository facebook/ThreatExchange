/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React, {useContext, useEffect, useState} from 'react';
import {
  Button,
  Card,
  Col,
  Container,
  Form,
  InputGroup,
  Modal,
  Row,
  Spinner,
} from 'react-bootstrap';
import {IonIcon} from '@ionic/react';
import {eyeOutline, eyeOffOutline} from 'ionicons/icons';
import {
  addNewExchange,
  fetchAllExchanges,
  getExchangeCredentialString,
  setExchangeCredentialString,
  updateExchangeStatus,
} from '../../Api';
import {NotificationsContext} from '../../AppWithNotifications';
import {Exchange} from '../../messages/ExchangeMessages';
import SettingsTabPane from './SettingsTabPane';

export function humanizeClassName(className: string) {
  const parts = className.split('.');
  return parts[parts.length - 1];
}

type CredentialControlProps = {
  cls: string;
};

function CredentialControl({cls}: CredentialControlProps): JSX.Element {
  const [showModal, setShowModal] = useState<boolean>(false);
  const [showCurrentCreds, setShowCurrentCreds] = useState<boolean>(false);
  const [currentCreds, setCurrentCreds] = useState<string>();
  const [newCredentialString, setNewCredentialString] = useState<string>();
  const [refetchCounter, setRefetchCounter] = useState<number>(1);

  const notifications = useContext(NotificationsContext);

  const humanized = humanizeClassName(cls);

  useEffect(() => {
    getExchangeCredentialString(cls).then(setCurrentCreds);
  }, [refetchCounter]);

  const handleUpdateCredentialString = () => {
    if (newCredentialString) {
      setExchangeCredentialString(cls, newCredentialString)
        .then(() => {
          notifications.info({message: 'Updated credentials.'});
          setShowModal(false);
          setNewCredentialString(undefined);
          setRefetchCounter(refetchCounter + 1);
        })
        .catch(() => {
          notifications.error({message: 'Could not update credentials.'});
        });
    }
  };

  return (
    <p>
      <Modal show={showModal} onHide={() => setShowModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Change credential string for {humanized}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {currentCreds === null ? (
            <Spinner animation="border" role="status" />
          ) : (
            <Container>
              <Row className="mb-4">
                <Col>
                  <Form.Label htmlFor="current-creds">
                    Current Credential String
                  </Form.Label>
                  <InputGroup>
                    <Form.Control
                      disabled
                      type={showCurrentCreds ? 'text' : 'password'}
                      value={currentCreds}
                      id="current-creds"
                    />
                    <InputGroup.Text
                      onClick={() => setShowCurrentCreds(!showCurrentCreds)}>
                      <IonIcon
                        icon={showCurrentCreds ? eyeOffOutline : eyeOutline}
                      />
                    </InputGroup.Text>
                  </InputGroup>
                </Col>
              </Row>
              <Row className="mb-4">
                <Col>
                  <Form.Label htmlFor="current-creds">
                    Set Credential String
                  </Form.Label>
                  <Form.Control
                    type="password"
                    value={newCredentialString}
                    id="current-creds"
                    onChange={e => setNewCredentialString(e.target.value)}
                  />
                </Col>
              </Row>
              <Row className="mb-4">
                <Col>
                  <Button
                    onClick={handleUpdateCredentialString}
                    disabled={
                      newCredentialString === '' ||
                      newCredentialString === undefined
                    }>
                    Update
                  </Button>
                </Col>
              </Row>
            </Container>
          )}
        </Modal.Body>
      </Modal>
      <Button variant="secondary" onClick={() => setShowModal(true)}>
        Change Credential String
      </Button>
    </p>
  );
}

export default function ExchangesTab(): JSX.Element {
  const [exchanges, setExchanges] = useState<{[key: string]: Exchange}>({});
  const [showAddNewExchange, setShowAddNewExchange] = useState<boolean>(false);
  const [newExchangeClass, setNewExchangeClass] = useState<string>();
  const [refetchCounter, setRefetchCounter] = useState<number>(1);
  const notifications = useContext(NotificationsContext);

  useEffect(() => {
    fetchAllExchanges().then(setExchanges);
  }, [refetchCounter]);

  const setUpdateStatus = (className: string, status: boolean) => {
    const message = status
      ? `Enabled ${humanizeClassName(className)}`
      : `Disabled ${humanizeClassName(className)}`;

    updateExchangeStatus(className, status).then(() => {
      notifications.success({
        message,
      });
    });

    const newExchanges: {[key: string]: Exchange} = {};
    Object.keys(exchanges).forEach(key => {
      if (key === className) {
        newExchanges[key] = {...exchanges[key], enabled: status};
      } else {
        newExchanges[key] = exchanges[key];
      }
    });

    setExchanges(newExchanges);
  };

  const handleNewExchangeClassAdd = () => {
    if (newExchangeClass) {
      addNewExchange(newExchangeClass)
        .then(() => {
          notifications.success({message: 'Added new Signal Exchange API.'});
          setRefetchCounter(refetchCounter + 1);
          setShowAddNewExchange(false);
        })
        .catch(() => {
          notifications.error({
            message: 'Could not add new Signal Exchange API.',
          });
        });
    }
  };

  const exchangeRows = Object.keys(exchanges).map(cxClass => {
    const humanName = humanizeClassName(cxClass);
    return (
      <Row key={cxClass} className="mt-2">
        <Col>
          <Card>
            <Card.Header>
              <div className="float-left">
                <code>{humanName}</code>
              </div>
              <div className="float-right">
                <Form>
                  <Form.Check
                    id={`enabled-${humanName}`}
                    type="switch"
                    label="Enabled"
                    checked={exchanges[cxClass].enabled}
                    onChange={() =>
                      setUpdateStatus(cxClass, !exchanges[cxClass].enabled)
                    }
                  />
                </Form>
              </div>
            </Card.Header>
            <Card.Body>
              <p>
                <b>Full Class Name:&nbsp;</b>
                <code>{cxClass}</code>
              </p>
              {exchanges[cxClass].supports_credentials ? (
                <CredentialControl cls={cxClass} />
              ) : null}
            </Card.Body>
          </Card>
        </Col>
      </Row>
    );
  });

  return (
    <SettingsTabPane>
      <Row>
        <Col>
          <SettingsTabPane.Title>Exchanges</SettingsTabPane.Title>
        </Col>
        <Col>
          <div className="float-right">
            <Button
              variant="success"
              onClick={() => setShowAddNewExchange(true)}>
              Add New Exchange
            </Button>
          </div>
        </Col>
      </Row>
      <Row className="mb-3">
        <Col>
          Exchanges are how you connect to other Signal sharing locations like
          Meta&apos;s ThreatExchange.
        </Col>
      </Row>
      <>{exchangeRows}</>
      <Modal
        show={showAddNewExchange}
        onHide={() => setShowAddNewExchange(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Add a new Signal Exchange Type</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Label htmlFor="new-exchange-class">
            Full classname for new signal exchange.
          </Form.Label>
          <Form.Control
            type="text"
            value={newExchangeClass}
            id="new-exchange-class"
            onChange={e => setNewExchangeClass(e.target.value)}
          />
          <div className="mt-3">
            <Button
              onClick={handleNewExchangeClassAdd}
              disabled={
                newExchangeClass === undefined || newExchangeClass === ''
              }>
              Add
            </Button>
          </div>
        </Modal.Body>
      </Modal>
    </SettingsTabPane>
  );
}
