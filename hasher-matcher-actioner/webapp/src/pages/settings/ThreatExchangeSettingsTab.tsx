/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React, {useEffect, useState, useContext} from 'react';
import {
  Row,
  Button,
  Spinner,
  Tooltip,
  OverlayTrigger,
  Card,
  Col,
  Alert,
} from 'react-bootstrap';
import classNames from 'classnames';
import {Link} from 'react-router-dom';
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
import {NotificationsContext} from '../../AppWithNotifications';
import SettingsTabPane from './SettingsTabPane';
import ThreatExchangeTokenEditor from './ThreatExchangeTokenEditor';
import EmptyState from '../../components/EmptyState';

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
  pdq_match_threshold?: string;
};

export default function ThreatExchangeSettingsTab(): JSX.Element {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const notifications = useContext(NotificationsContext);

  const onPrivacyGroupSave = (privacyGroup: PrivacyGroup) => {
    updateDataset(
      privacyGroup.privacyGroupId,
      privacyGroup.localFetcherActive,
      privacyGroup.localWriteBack,
      privacyGroup.localMatcherActive,
      privacyGroup.localPDQMatchThreshold,
    )
      .then(response => {
        notifications.success({message: 'Changes are saved!'});
        datasets[
          datasets.findIndex(
            item => item.privacy_group_id === response.privacy_group_id,
          )
        ] = response;
        setDatasets(datasets);
      })
      .catch(() => {
        notifications.error({
          message: 'Errors when saving changes. Please try again later',
        });
      });
  };
  const onPrivacyGroupDelete = (privacyGroupId: string) => {
    deleteDataset(privacyGroupId)
      .then(response => {
        notifications.success({message: response.response});
        const filteredDatasets = datasets.filter(
          item => item.privacy_group_id !== privacyGroupId,
        );
        setDatasets(filteredDatasets);
      })
      .catch(() => {
        notifications.error({
          message:
            'Errors when deleting the privacy group. Please try again later',
        });
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
        notifications.error({
          message: `Errors when fetching privacy groups. Please try again later\n ${e.message}`,
        });
      });
  };

  const onSync = () => {
    setSyncing(true);
    syncAllDatasets()
      .then(syncResponse => {
        setSyncing(false);
        notifications.success({message: syncResponse.response});
        refreshDatasets();
      })
      .catch(() => {
        setSyncing(false);
        notifications.error({
          message: 'Errors when syncing privacy groups. Please try again later',
        });
      });
  };

  useEffect(() => {
    refreshDatasets();
  }, []);
  return (
    <SettingsTabPane>
      <Row>
        <Col>
          <Alert variant="warning">
            <Alert.Heading>Warning</Alert.Heading>
            <p>
              We are now recommending you use the{' '}
              <Link to="/collabs/">Collaborations</Link> feature to manage your
              ThreatExchange Privacy Groups.
            </p>
          </Alert>
        </Col>
      </Row>
      <Row className="mt-3">
        <Col xs={{span: 8}}>
          <h3>ThreatExchange Datasets </h3>
        </Col>
        <Col
          xs={{span: 4}}
          className={classNames({
            'text-right': true,
            // Only show the sync button if not we have datasets, otherwise
            // there will be two CTAs (in the empty state and this one)
            invisible: !loading && (!datasets || datasets.length === 0),
          })}>
          <OverlayTrigger
            key="syncButton"
            placement="left"
            overlay={
              <Tooltip id="sync-info" className="p-2">
                <p style={{textAlign: 'left'}}>
                  Get information on all PrivacyGroups that you have access to.
                  These will be used to fetch datasets of hashes.
                </p>
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
        </Col>
      </Row>
      <Row className="mt-3">
        {loading ? (
          <Col>
            <Spinner animation="border" role="status">
              <span className="sr-only">Loading...</span>
            </Spinner>
          </Col>
        ) : null}

        {!loading && (!datasets || datasets.length === 0) ? (
          <EmptyState>
            <EmptyState.Lead>No ThreatExchange Datasets found</EmptyState.Lead>

            <p>
              Datasets map to{' '}
              <a href="https://developers.facebook.com/docs/threat-exchange/reference/apis/threat-privacy-group/v12.0">
                Threat Privacy Groups
              </a>{' '}
              on ThreatExchange. Use the sync button to fetch all privacy groups
              you have access to.
            </p>
            <EmptyState.CTA onClick={onSync}>Sync</EmptyState.CTA>
          </EmptyState>
        ) : (
          datasets.map(dataset => (
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
              pdqMatchThreshold={dataset.pdq_match_threshold}
              onSave={onPrivacyGroupSave}
              onDelete={onPrivacyGroupDelete}
            />
          ))
        )}
      </Row>
      <Row>
        <Col>
          <hr />
        </Col>
      </Row>

      <Row className="mt-3">
        <Col>
          <h3>ThreatExchange Configuration</h3>
        </Col>
      </Row>
      <Row>
        <Col xs={{span: 8}}>
          <ThreatExchangeTokenEditor />
        </Col>
      </Row>
      <Row>
        <Col>
          <hr />
        </Col>
      </Row>

      <Row className="mt-3">
        <Col className="mx-1" md="8">
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
      </Row>
    </SettingsTabPane>
  );
}
