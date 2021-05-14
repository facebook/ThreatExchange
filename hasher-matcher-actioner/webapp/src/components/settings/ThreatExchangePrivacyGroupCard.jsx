import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {
  Col,
  Button,
  Form,
  Card,
  OverlayTrigger,
  Popover,
} from 'react-bootstrap';
import DOMPurify from 'dompurify';
import {CopyableTextField} from '../../utils/TextFieldsUtils';

export default function ThreatExchangePrivacyGroupCard({
  fetcherActive,
  matcherActive,
  inUse,
  privacyGroupId,
  privacyGroupName,
  description,
  writeBack,
  hashCount,
  lastModified,
  onSave,
  onDelete,
}) {
  const [originalFetcherActive, setOriginalFetcherActive] = useState(
    fetcherActive,
  );
  const [originalWriteBack, setOriginalWriteBack] = useState(writeBack);
  const [originalMatcherActive, setOriginalMatcherActive] = useState(
    matcherActive,
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

  return (
    <>
      <Col lg={4} sm={6} xs={12} className="mb-4">
        <Card className="text-center">
          <Card.Header
            className={
              inUse ? 'text-white bg-primary' : 'text-white bg-secondary'
            }>
            <h4 className="mb-0">
              <CopyableTextField text={privacyGroupName} color="white" />
              <OverlayTrigger
                trigger="focus"
                placement="bottom"
                overlay={
                  <Popover id={`popover-basic${privacyGroupId}`}>
                    <Popover.Title as="h3">Information</Popover.Title>
                    <Popover.Content>
                      <div
                        dangerouslySetInnerHTML={{
                          __html: DOMPurify.sanitize(`${description}`, {
                            ADD_ATTR: ['target'],
                          }),
                        }}
                      />
                    </Popover.Content>
                  </Popover>
                }>
                <Button class="btn btn-primary btn-circle">
                  <ion-icon name="information-circle-outline" size="large" />
                </Button>
              </OverlayTrigger>
            </h4>
          </Card.Header>
          <Card.Subtitle className="mt-2 mb-2 text-muted">
            <CopyableTextField text={privacyGroupId} />
          </Card.Subtitle>
          <Card.Body className="text-left">
            <Form>
              <div>
                <OverlayTrigger
                  trigger="focus"
                  placement="bottom"
                  overlay={
                    <Popover id={`popover-hashCount${privacyGroupId}`}>
                      <Popover.Title as="h3">Hash Count</Popover.Title>
                      <Popover.Content>{hashCount}</Popover.Content>
                    </Popover>
                  }>
                  <Button variant="info">Hash Count</Button>
                </OverlayTrigger>{' '}
                <OverlayTrigger
                  trigger="focus"
                  placement="bottom"
                  overlay={
                    <Popover id={`popover-lastModified${privacyGroupId}`}>
                      <Popover.Title as="h3">Last Modified Time</Popover.Title>
                      <Popover.Content>{lastModified}</Popover.Content>
                    </Popover>
                  }>
                  <Button variant="info">Last Modified Time</Button>
                </OverlayTrigger>
              </div>
              <Form.Switch
                onChange={onSwitchFetcherActive}
                id={`fetcherActiveSwitch${privacyGroupId}`}
                label="Fetcher Active"
                checked={localFetcherActive}
                disabled={!inUse}
                style={{marginTop: 10}}
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
                label="Write Back"
                checked={localWriteBack}
                disabled={!inUse}
              />
            </Form>
          </Card.Body>
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

ThreatExchangePrivacyGroupCard.propTypes = {
  fetcherActive: PropTypes.bool.isRequired,
  matcherActive: PropTypes.bool.isRequired,
  inUse: PropTypes.bool.isRequired,
  privacyGroupId: PropTypes.number.isRequired,
  privacyGroupName: PropTypes.string.isRequired,
  description: PropTypes.string.isRequired,
  writeBack: PropTypes.bool.isRequired,
  hashCount: PropTypes.number.isRequired,
  lastModified: PropTypes.string.isRequired,
  onSave: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
};
