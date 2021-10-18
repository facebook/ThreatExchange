/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useEffect, useState} from 'react';
import {
  Row,
  Button,
  Toast,
  Spinner,
  Tooltip,
  OverlayTrigger,
  Card,
  Col,
} from 'react-bootstrap';
import ThreatExchangePrivacyGroupCard from '../../components/settings/ThreatExchangePrivacyGroupCard';
import {
  HolidaysDatasetInformationBlock,
  SAMPLE_PG_ID,
} from '../../components/HolidaysDatasetInformationBlock';
import {
  PrivacyGroup,
  fetchAllDatasets,
  syncAllDatasets,
  updateDataset,
  deleteDataset,
} from '../../Api';

type Dataset = {
  privacy_group_id: string;
  privacy_group_name: string;
  description: string;
  fetcher_active: boolean;
  matcher_active: boolean;
  in_use: boolean;
  write_back: boolean;
  hash_count: number;
  match_count: number;
};

export default function ThreatExchangeSettingsTab(): JSX.Element {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [showToast, setShowToast] = useState(false);
  const [toastBody, setToastBody] = useState('');
  const onPrivacyGroupSave = (privacyGroup: PrivacyGroup) => {
    updateDataset(
      privacyGroup.privacyGroupId,
      privacyGroup.localFetcherActive,
      privacyGroup.localWriteBack,
      privacyGroup.localMatcherActive,
    )
      .then(response => {
        setToastBody('Changes are saved!');
        setShowToast(true);
        datasets[
          datasets.findIndex(
            item => item.privacy_group_id === response.privacy_group_id,
          )
        ] = response;
        setDatasets(datasets);
      })
      .catch(() => {
        setToastBody('Errors when saving changes. Please try again later');
        setShowToast(true);
      });
  };
  const onPrivacyGroupDelete = (privacyGroupId: string) => {
    deleteDataset(privacyGroupId)
      .then(response => {
        setToastBody(response.response);
        setShowToast(true);
        const filteredDatasets = datasets.filter(
          item => item.privacy_group_id !== privacyGroupId,
        );
        setDatasets(filteredDatasets);
      })
      .catch(() => {
        setToastBody(
          'Errors when deleting the privacy group. Please try again later',
        );
        setShowToast(true);
      });
  };

  const refreshDatasets = () => {
    setLoading(true);
    fetchAllDatasets()
      .then(response => {
        setLoading(false);
        setDatasets(response.threat_exchange_datasets);
      })
      .catch(e => {
        setLoading(false);
        setToastBody(
          `Errors when fetching privacy groups. Please try again later\n ${e.message}`,
        );
        setShowToast(true);
      });
  };

  const onSync = () => {
    setSyncing(true);
    syncAllDatasets()
      .then(syncResponse => {
        setSyncing(false);
        setToastBody(syncResponse.response);
        setShowToast(true);
        refreshDatasets();
      })
      .catch(() => {
        setSyncing(false);
        setToastBody(
          'Errors when syncing privacy groups. Please try again later',
        );
        setShowToast(true);
      });
  };

  useEffect(() => {
    refreshDatasets();
  }, []);
  return (
    <>
      <div className="feedback-toast-container">
        <Toast onClose={() => setShowToast(false)} show={showToast} autohide>
          <Toast.Body>{toastBody}</Toast.Body>
        </Toast>
      </div>
      <Card.Header>
        <Row className="mt-3">
          <h2 className="mt-2">ThreatExchange Datasets </h2>
          <OverlayTrigger
            key="syncButton"
            placement="right"
            overlay={
              <Tooltip id="tooltip-right">
                Read PrivacyGroup metatdata from ThreatExchange to build new
                Datasets
              </Tooltip>
            }>
            <Button
              variant="primary"
              disabled={syncing}
              onClick={() => {
                onSync();
              }}
              style={{marginLeft: 10}}>
              <Spinner
                hidden={!syncing}
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
        <Row className="mt-3">
          <Spinner hidden={!loading} animation="border" role="status">
            <span className="sr-only">Loading...</span>
          </Spinner>
          {!datasets || datasets.length === 0
            ? null
            : datasets.map(dataset => (
                <ThreatExchangePrivacyGroupCard
                  key={dataset.privacy_group_id}
                  privacyGroupName={dataset.privacy_group_name}
                  description={dataset.description}
                  fetcherActive={dataset.fetcher_active}
                  matcherActive={dataset.matcher_active}
                  inUse={dataset.in_use}
                  privacyGroupId={dataset.privacy_group_id}
                  writeBack={dataset.write_back}
                  hashCount={dataset.hash_count}
                  matchCount={dataset.match_count}
                  onSave={onPrivacyGroupSave}
                  onDelete={onPrivacyGroupDelete}
                />
              ))}
        </Row>
      </Card.Body>
      <Col className="mx-1" md="6">
        <HolidaysDatasetInformationBlock
          samplePGExists={
            datasets
              ? datasets.some(
                  (ds: {privacy_group_id: string}) =>
                    ds.privacy_group_id === SAMPLE_PG_ID,
                )
              : false
          }
          refresh={refreshDatasets}
        />
      </Col>
    </>
  );
}
