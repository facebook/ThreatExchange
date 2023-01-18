/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React, {useState} from 'react';
import {IonIcon} from '@ionic/react';
import {chevronUp, chevronDown} from 'ionicons/icons';
import {useFormik} from 'formik';

import {Accordion, Col, Button, Form, Card} from 'react-bootstrap';
import DOMPurify from 'dompurify';
import {CopyableTextField} from '../../utils/TextFieldsUtils';
import {PrivacyGroup} from '../../Api';

type AdvancedSettingsValues = {
  pdqMatchThreshold?: string;
};

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
  pdqMatchThreshold?: string;
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
  /* eslint-disable @typescript-eslint/no-unused-vars */
  matchCount,
  /* eslint-enable @typescript-eslint/no-unused-vars */
  pdqMatchThreshold,
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
  const [originalPDQMatchThreshold, setOriginalPDQMatchThreshold] = useState(
    pdqMatchThreshold ?? '',
  );
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

  function validate(values: AdvancedSettingsValues) {
    const errors: Partial<AdvancedSettingsValues> = {};
    if (
      !!values.pdqMatchThreshold &&
      (Number.isNaN(Number(values.pdqMatchThreshold)) ||
        Number(values.pdqMatchThreshold) < 0 ||
        Number(values.pdqMatchThreshold) > 52)
    ) {
      errors.pdqMatchThreshold =
        'Nonempty values must be between 0 (for only exact matches) and 52 (max threshold supported by index) inclusive';
    }

    return errors;
  }

  const formik = useFormik({
    initialValues: {
      pdqMatchThreshold: pdqMatchThreshold ?? '',
    },
    validate,
    /* eslint-disable @typescript-eslint/no-unused-vars */
    onSubmit: _ => {
      /* eslint-enable @typescript-eslint/no-unused-vars */
      // https://github.com/jaredpalmer/formik/issues/2675
      // this should never trigger but due to typing we can't just omit it.
    },
  });

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
                    icon={showDescription ? chevronUp : chevronDown}
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
                  icon={showAdvancedSettings ? chevronUp : chevronDown}
                />
              </Accordion.Toggle>
              <Accordion.Collapse className="mt-2 mr-2" eventKey="0">
                <Card.Body>
                  <Form>
                    <Form.Group>
                      <Form.Label>Custom PDQ Match Threshold</Form.Label>
                      <Form.Control
                        id="pdqMatchThreshold"
                        onBlur={formik.handleBlur}
                        isValid={
                          formik.touched.pdqMatchThreshold &&
                          !formik.errors.pdqMatchThreshold &&
                          formik.values.pdqMatchThreshold !==
                            originalPDQMatchThreshold
                        }
                        isInvalid={
                          formik.touched.pdqMatchThreshold &&
                          !!formik.errors.pdqMatchThreshold
                        }
                        onChange={formik.handleChange}
                        type="text"
                        value={formik.values.pdqMatchThreshold}
                        placeholder="None"
                      />
                      {formik.touched.pdqMatchThreshold &&
                      formik.errors.pdqMatchThreshold ? (
                        <Form.Control.Feedback type="invalid">
                          {formik.errors.pdqMatchThreshold}
                        </Form.Control.Feedback>
                      ) : null}
                    </Form.Group>
                  </Form>
                </Card.Body>
              </Accordion.Collapse>
            </Accordion>
          </Card>

          <Card.Footer>
            {localWriteBack === originalWriteBack &&
            localFetcherActive === originalFetcherActive &&
            localMatcherActive === originalMatcherActive &&
            (!formik.touched.pdqMatchThreshold ||
              formik.values.pdqMatchThreshold ===
                originalPDQMatchThreshold) ? null : (
              <div>
                <Button
                  variant="primary"
                  onClick={() => {
                    setOriginalFetcherActive(localFetcherActive);
                    setOriginalWriteBack(localWriteBack);
                    setOriginalMatcherActive(localMatcherActive);
                    setOriginalPDQMatchThreshold(
                      formik.values.pdqMatchThreshold,
                    );
                    onSave({
                      privacyGroupId,
                      localFetcherActive,
                      localWriteBack,
                      localMatcherActive,
                      localPDQMatchThreshold: formik.values.pdqMatchThreshold,
                    });
                  }}
                  disabled={!!formik.errors.pdqMatchThreshold}>
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

ThreatExchangePrivacyGroupCard.defaultProps = {
  pdqMatchThreshold: undefined,
};
