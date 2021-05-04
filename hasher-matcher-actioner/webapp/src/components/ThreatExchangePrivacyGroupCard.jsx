import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Col, Button, Form, Card} from 'react-bootstrap';
import {CopyableTextField} from '../utils/TextFieldsUtils';

export default function ThreatExchangePrivacyGroupCard({
  fetcherActive,
  inUse,
  privacyGroupId,
  privacyGroupName,
  writeBack,
  onSave,
  onDelete,
}) {
  const [originalFetcherActive, setOriginalFetcherActive] = useState(
    fetcherActive,
  );
  const [originalWriteBack, setOriginalWriteBack] = useState(writeBack);
  const [localFetcherActive, setLocalFetcherActive] = useState(fetcherActive);
  const [localWriteBack, setLocalWriteBack] = useState(writeBack);
  const onSwitchFetcherActive = () => {
    setLocalFetcherActive(!localFetcherActive);
  };
  const onSwitchWriteBack = () => {
    setLocalWriteBack(!localWriteBack);
  };

  return (
    <>
      <Col lg={4} sm={6} xs={12} className="mb-4">
        <Card className="text-center">
          <Card.Header
            className={
              inUse ? 'text-white bg-success' : 'text-white bg-secondary'
            }>
            <h4 className="mb-0">{privacyGroupName}</h4>
          </Card.Header>
          <Card.Subtitle className="mt-2 mb-2 text-muted">
            <CopyableTextField text={privacyGroupId} />
          </Card.Subtitle>
          <Card.Body className="text-left">
            <Form>
              <Form.Switch
                onChange={onSwitchFetcherActive}
                id={`fetcherActiveSwitch${privacyGroupId}`}
                label="Fetcher Active"
                checked={localFetcherActive}
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
            localFetcherActive === originalFetcherActive ? null : (
              <div>
                <Button
                  variant="primary"
                  onClick={() => {
                    setOriginalFetcherActive(localFetcherActive);
                    setOriginalWriteBack(localWriteBack);
                    onSave({
                      privacyGroupId,
                      localFetcherActive,
                      localWriteBack,
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
  inUse: PropTypes.bool.isRequired,
  privacyGroupId: PropTypes.number.isRequired,
  privacyGroupName: PropTypes.string.isRequired,
  writeBack: PropTypes.bool.isRequired,
  onSave: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
};
