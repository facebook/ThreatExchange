/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useEffect, useState} from 'react';
import Tab from 'react-bootstrap/Tab';
import Tabs from 'react-bootstrap/Tabs';
import {useHistory, useParams} from 'react-router-dom';
import {fetchAllActionRules, fetchAllActions} from '../Api';
import ActionRuleSettingsTab, {
  ActionRule,
} from './settings/ActionRuleSettingsTab';
import ActionPerformerSettingsTab, {
  ActionPerformer,
} from './settings/ActionPerformerSettingsTab';
import ThreatExchangeSettingsTab from './settings/ThreatExchangeSettingsTab';
import IndexSettingsTab from './settings/IndexSettingsTab';

// This array must include the eventKey attribute value of any Tab in Tabs as
// a part of the implementation to give each tab its own route.
const tabEventKeys = ['threatexchange', 'actions', 'action-rules'];

export default function Settings(): JSX.Element {
  const {tab = tabEventKeys[0]} = useParams<{tab: string}>();
  const history = useHistory();
  const [actions, setActions] = useState<ActionPerformer[]>([]);
  const [actionRules, setActionRules] = useState<ActionRule[]>([]);

  useEffect(() => {
    fetchAllActionRules().then(fetchedActionRules => {
      setActionRules(fetchedActionRules);
    });
  }, []);

  useEffect(() => {
    fetchAllActions().then(fetchedActions => {
      setActions(fetchedActions);
    });
  }, []);

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
          <ActionPerformerSettingsTab
            actions={actions}
            setActions={setActions}
            actionRules={actionRules}
          />
        </Tab>
        <Tab eventKey="action-rules" title="Action Rules">
          <ActionRuleSettingsTab
            actions={actions}
            actionRules={actionRules}
            setActionRules={setActionRules}
          />
        </Tab>
        <Tab eventKey="index" title="Indexes">
          <IndexSettingsTab />
        </Tab>
      </Tabs>
    </>
  );
}
