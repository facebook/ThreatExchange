/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';
import Tab from 'react-bootstrap/Tab';
import Tabs from 'react-bootstrap/Tabs';
import {useHistory, useParams} from 'react-router-dom';
import ActionRuleSettingsTab from './settings/ActionRuleSettingsTab';
import ActionSettingsTab from './settings/ActionSettingsTab';
import ThreatExchangeSettingsTab from './settings/ThreatExchangeSettingsTab';

export default function Settings() {
  const {tab} = useParams();
  const history = useHistory();
  if (
    tab === undefined ||
    !tab ||
    (tab !== 'threatexchange' &&
      tab !== 'pipeline' &&
      tab !== 'actions' &&
      tab !== 'action-rules')
  ) {
    window.location = '/settings/threatexchange';
  }
  return (
    <>
      <Tabs
        activeKey={tab}
        id="setting-tabs"
        onSelect={key => {
          history.push(`/settings/${key}`);
        }}>
        <Tab eventKey="threatexchange" title="ThreatExchange">
          <ThreatExchangeSettingsTab />
        </Tab>
        <Tab eventKey="pipeline" title="Pipeline">
          Todo!
        </Tab>
        <Tab eventKey="actions" title="Actions">
          <ActionSettingsTab />
        </Tab>
        <Tab eventKey="action-rules" title="Action Rules">
          <ActionRuleSettingsTab />
        </Tab>
      </Tabs>
    </>
  );
}
