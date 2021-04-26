/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';
import Tab from 'react-bootstrap/Tab';
import Tabs from 'react-bootstrap/Tabs';
import ActionSettingsTab from './settings/ActionSettingsTab';
import SignalSettingsTab from './settings/SignalSettingsTab';

export default function Settings() {
  return (
    <>
      <Tabs defaultActiveKey="signals" id="setting-tabs">
        <Tab eventKey="signals" title="Signals">
          <SignalSettingsTab />
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
