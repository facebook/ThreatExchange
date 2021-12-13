/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState} from 'react';
import {IonIcon} from '@ionic/react';
import {chevronUp, chevronDown} from 'ionicons/icons';

import {Accordion, Col, Button, Form, Card} from 'react-bootstrap';
import DOMPurify from 'dompurify';
import {CopyableTextField} from '../../utils/TextFieldsUtils';
import {PrivacyGroup} from '../../Api';

type ThreatExchangePrivacyGroupCardProps = {
  fetcherActive: boolean;
  matcherActive: boolean;
  inUse: boolean;
  privacyGroupId: string;
  privacyGroupName: string;
  description: string;
  writeBack: boolean;
  hashCount: number;
  matchCount: number;
  onSave: (pg: PrivacyGroup) => void;
  onDelete: (privacyGroupId: string) => void;
};

export default function ThreatExchangePrivacyGroupCard({
  fetcherActive,
  matcherActive,
  inUse,
  privacyGroupId,
  privacyGroupName,
  description,
  writeBack,
  hashCount,
  matchCount,
  onSave,
  onDelete,
}: ThreatExchangePrivacyGroupCardProps): JSX.Element {
  const [showDescription, setShowDescription] = useState(false);
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);

  const [originalFetcherActive, setOriginalFetcherActive] =
    useState(fetcherActive);
  const [originalWriteBack, setOriginalWriteBack] = useState(writeBack);
  const [originalMatcherActive, setOriginalMatcherActive] =
    useState(matcherActive);
  const [localFetcherActive, setLocalFetcherActive] = useState(fetcherActive);
  const [localWriteBack, setLocalWriteBack] = useState(writeBack);
  const [localMatcherActive, setLocalMatcherActive] = useState(matcherActive);
  const onSwitchFetcherActive = () => {
    setLocalFetcherActive(!localFetcherActive);
  };
  const onSwitchWriteBack = () => {
    setLocalWriteBack(!localWriteBack);
  };
  const onSwitchMatcherActive = () => {
    setLocalMatcherActive(!localMatcherActive);
  };

  return (
    <>
      <Col lg={4} sm={6}>
        <Card className="mb-2">
          <Card.Header className="mb-2 text-center">
            {privacyGroupName}
          </Card.Header>
          <Card className="mx-2 mb-2">
            <Card.Subtitle className="ml-3 my-2">
              Dataset ID: <CopyableTextField text={privacyGroupId} />
              <Accordion>
                <Accordion.Toggle
                  eventKey="0"
                  as={Button}
                  variant="outline-dark"
                  size="sm"
                  disabled={!description}
                  onClick={() => setShowDescription(!showDescription)}
                  className="my-2">
                  Description
                  <IonIcon
                    className="inline-icon"
                    icon={showDescription ? chevronDown : chevronUp}
                  />
                </Accordion.Toggle>
                <Accordion.Collapse
                  as={Card.Text}
                  className="mt-2 mr-2 text-muted"
                  eventKey="0">
                  <div
                    dangerouslySetInnerHTML={{
                      __html: DOMPurify.sanitize(`${description}`, {
                        ADD_ATTR: ['target'],
                      }),
                    }}
                  />
                </Accordion.Collapse>
              </Accordion>
            </Card.Subtitle>
          </Card>
          <Card className="mx-2 mb-2">
            <Card.Body className="text-left">
              {/* ToDo move to table based on signal type in own subcard. */}
              <Card.Text>PDQ Hashes Available: {hashCount} </Card.Text>
              <Form>
                <Form.Switch
                  onChange={onSwitchFetcherActive}
                  id={`fetcherActiveSwitch${privacyGroupId}`}
                  label="Fetcher Active"
                  checked={localFetcherActive}
                  disabled={!inUse}
                />
                <Form.Switch
                  onChange={onSwitchMatcherActive}
                  id={`matcherSwitch${privacyGroupId}`}
                  label="Matcher Active"
                  checked={localMatcherActive}
                  disabled={!inUse}
                />
                <Form.Switch
                  onChange={onSwitchWriteBack}
                  id={`writeBackSwitch${privacyGroupId}`}
                  label="Writeback Seen"
                  checked={localWriteBack}
                  disabled={!inUse}
                />
              </Form>
            </Card.Body>
          </Card>
          <Card className="mx-2 mb-2 text-left">
            <Accordion>
              <Accordion.Toggle
                eventKey="0"
                as={Card.Header}
                onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}
                variant="outline-dark"
                size="sm"
                className="mb-2 text-muted">
                {!showAdvancedSettings
                  ? 'Show Advanced Settings '
                  : 'Hide Advanced Settings '}
                <IonIcon
                  className="inline-icon"
                  icon={showAdvancedSettings ? chevronDown : chevronUp}
                />
              </Accordion.Toggle>
              <Accordion.Collapse className="mt-2 mr-2 text-muted" eventKey="0">
                <Card.Body>Comming Soon!</Card.Body>
              </Accordion.Collapse>
            </Accordion>
          </Card>

          <Card.Footer>
            {localWriteBack === originalWriteBack &&
            localFetcherActive === originalFetcherActive &&
            localMatcherActive === originalMatcherActive ? null : (
              <div>
                <Button
                  variant="primary"
                  onClick={() => {
                    setOriginalFetcherActive(localFetcherActive);
                    setOriginalWriteBack(localWriteBack);
                    setOriginalMatcherActive(localMatcherActive);
                    onSave({
                      privacyGroupId,
                      localFetcherActive,
                      localWriteBack,
                      localMatcherActive,
                    });
                  }}>
                  Save
                </Button>
              </div>
            )}
            {inUse ? null : (
              <div>
                <Button
                  variant="secondary"
                  onClick={() => {
                    onDelete(privacyGroupId);
                  }}>
                  Delete
                </Button>
              </div>
            )}
          </Card.Footer>
        </Card>
      </Col>
    </>
  );
}
