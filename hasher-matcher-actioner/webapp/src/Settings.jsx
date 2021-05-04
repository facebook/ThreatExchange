/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';
import Tab from 'react-bootstrap/Tab';
import Tabs from 'react-bootstrap/Tabs';
import ActionSettingsTab from './settings/ActionSettingsTab';
import ThreatExchangeSettingsTab from './settings/ThreatExchangeSettingsTab';

export default function Settings() {
  return (
    <>
      <Tabs defaultActiveKey="threatexchange" id="setting-tabs">
        <Tab eventKey="threatexchange" title="ThreatExchange">
          <ThreatExchangeSettingsTab />
        </Tab>
        <Tab eventKey="pipeline" title="Pipeline">
          Todo!
        </Tab>
        <Tab eventKey="actions" title="Actions">
          <ActionSettingsTab />
        </Tab>
      </Tabs>
    </>
  );
}
