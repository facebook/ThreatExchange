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

// This array must include the eventKey attribute value of any Tab in Tabs as
// a part of the implementation to give each tab its own route.
const tabEventKeys = ['threatexchange', 'actions', 'action-rules'];

export default function Settings() {
  const {tab} = useParams<{tab: string}>();
  const history = useHistory();
  if (tab === undefined || !tab || !tabEventKeys.includes(tab)) {
    window.location.href = '/settings/threatexchange';
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
