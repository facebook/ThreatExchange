/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useEffect, useState} from 'react';
import {
  Col,
  Row,
  Button,
  Toast,
  Form,
  Spinner,
  Tooltip,
  OverlayTrigger,
  Card,
} from 'react-bootstrap';
import PropTypes from 'prop-types';
import {CopyableTextField} from '../utils/TextFieldsUtils';
import {
  fetchAllDatasets,
  syncAllDatasets,
  udpateDataset,
  deleteDataset,
} from '../Api';

export default function ThreatExchangeSettingsTab() {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(true);
  const [showToast, setShowToast] = useState(false);
  const [toastBody, setToastBody] = useState(null);
  const onPrivacyGroupSave = privacyGroup => {
    udpateDataset(
      privacyGroup.privacyGroupId,
      privacyGroup.localFetcherActive,
      privacyGroup.localWriteBack,
    ).then(response => {
      datasets[
        datasets.findIndex(
          item => item.privacy_group_id === response.privacy_group_id,
        )
      ] = response;
      setDatasets(datasets);
    });
  };
  const onPrivacyGroupDelete = privacyGroupId => {
    deleteDataset(privacyGroupId).then(() => {
      const filteredDatasets = datasets.filter(
        item => item.privacy_group_id !== privacyGroupId,
      );
      setDatasets(filteredDatasets);
    });
  };
  const onSync = () => {
    syncAllDatasets().then(syncResponse => {
      setSyncing(true);
      if (syncResponse.response === 'Dataset is update-to-date') {
        fetchAllDatasets().then(response => {
          setDatasets(response.datasets_response);
        });
      } else {
        alert('Errors when syncing privacy groups. Please try again later');
      }
    });
  };
  useEffect(() => {
    fetchAllDatasets(setLoading(false)).then(response => {
      setLoading(true);
      setDatasets(response.datasets_response);
    });
  }, []);
  return (
    <>
      <Card.Header>
        <Row className="mt-3">
          <h2 className="mt-2">ThreatExchange Privacy Groups </h2>
          <OverlayTrigger
            key="syncButton"
            placement="right"
            overlay={
              <Tooltip id="tooltip-right">
                Fetch privacy groups from ThreatExchange
              </Tooltip>
            }>
            <Button
              variant="primary"
              onClick={() => {
                setSyncing(false);
                setToastBody('Privacy groups are up to date!');
                setShowToast(true);
                onSync();
              }}
              style={{marginLeft: 10}}>
              <Spinner
                hidden={syncing}
                as="span"
                animation="border"
                size="sm"
                role="status"
                aria-hidden="true"
              />
              <span className="sr-only">Loading...</span>
              Sync
            </Button>
          </OverlayTrigger>
        </Row>
      </Card.Header>
      <Card.Body>
        <Toast onClose={() => setShowToast(false)} show={showToast} autohide>
          <Toast.Body>{toastBody}</Toast.Body>
        </Toast>
        <Row className="mt-3">
          <Spinner hidden={loading} animation="border" role="status">
            <span className="sr-only">Loading...</span>
          </Spinner>
          {datasets.length === 0
            ? null
            : datasets.map(dataset => (
                <ThreatExchangePrivacyGroupCard
                  key={dataset.privacy_group_id}
                  privacyGroupName={dataset.privacy_group_name}
                  fetcherActive={dataset.fetcher_active}
                  inUse={dataset.in_use}
                  privacyGroupId={dataset.privacy_group_id}
                  writeBack={dataset.write_back}
                  onSave={onPrivacyGroupSave}
                  onDelete={onPrivacyGroupDelete}
                  setShowToast={setShowToast}
                  setToastBody={setToastBody}
                />
              ))}
        </Row>
      </Card.Body>
    </>
  );
}

function ThreatExchangePrivacyGroupCard({
  fetcherActive,
  inUse,
  privacyGroupId,
  privacyGroupName,
  writeBack,
  onSave,
  onDelete,
  setShowToast,
  setToastBody,
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
                    setToastBody('Changes are saved!');
                    setShowToast(true);
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
                    setToastBody('The privacy group is deleted!');
                    setShowToast(true);
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
  setShowToast: PropTypes.func.isRequired,
  setToastBody: PropTypes.func.isRequired,
};
