/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

/* eslint-disable react/prop-types */

import Button from 'react-bootstrap/Button';
import Col from 'react-bootstrap/Col';
import React, {useContext, useState} from 'react';
import Row from 'react-bootstrap/Row';
import Table from 'react-bootstrap/Table';
import {RuleTester} from 'eslint';
import ActionRuleRow from '../../components/settings/ActionRuleRow';
import {addActionRule, deleteActionRule, updateActionRule} from '../../Api';
import {ActionPerformer} from './ActionPerformerSettingsTab';
import SettingsTabPane from './SettingsTabPane';
import {NotificationsContext} from '../../AppWithNotifications';
import EmptyState from '../../components/EmptyState';
import {ActionRule} from '../../messages/ActionMessages';
import '../../styles/_settings.scss';

const defaultActionRule = {
  name: '',
  must_have_labels: [],
  must_not_have_labels: [],
  action_label: {key: 'Action', value: ''},
};

type Input = {
  actions: ActionPerformer[];
  actionRules: ActionRule[];
  setActionRules: (actionRules: ActionRule[]) => void;
};

export default function ActionRuleSettingsTab({
  actions,
  actionRules,
  setActionRules,
}: Input): JSX.Element {
  const [adding, setAdding] = useState(false);
  const notifications = useContext(NotificationsContext);

  const actionRuleNameIsUnique = (
    newName: string,
    oldName: string,
  ): boolean => {
    if (newName) {
      const nameLower = newName.toLowerCase();

      const actionRuleIndex = actionRules.findIndex(
        actionRule => actionRule.name.toLowerCase() === nameLower,
      );

      return actionRuleIndex === -1 ? true : newName === oldName;
    }

    return true;
  };

  const onAddActionRule = (actionRule: ActionRule) => {
    setAdding(false);

    actionRules.splice(0, 0, actionRule);

    setActionRules([...actionRules]);
    addActionRule(actionRule).then(() => {
      notifications.success({
        message: 'A new action rule was added successfully.',
      });
    });
  };

  const onDeleteActionRule = (name: string) => {
    const indexToDelete = actionRules.findIndex(
      actionRule => actionRule.name === name,
    );
    actionRules.splice(indexToDelete, 1);
    setActionRules([...actionRules]);
    deleteActionRule(name);
    notifications.success({
      message: 'The action rule was deleted successfully.',
    });
  };

  const onUpdateActionRule = (
    oldName: string,
    updatedActionRule: ActionRule,
  ) => {
    // Optimistic UI update
    setActionRules(
      actionRules.map(rule => {
        if (rule.name === oldName) {
          return updatedActionRule;
        }

        return rule;
      }),
    );

    updateActionRule(oldName, updatedActionRule)
      .then(() => {
        notifications.success({
          message: 'The action rule was updated successfully.',
        });
      })
      .catch(() => {
        notifications.error({
          message: 'There was an error in updating the action rule.',
        });
      });
  };

  // Show empty state, and hide primary add action rule button.
  const actionRulesEmpty = actionRules.length === 0;

  return (
    <SettingsTabPane>
      <Row>
        <Col xs={{span: 9}}>
          <SettingsTabPane.Title>Action Rules</SettingsTabPane.Title>
        </Col>
        <Col xs={{span: 3}} className="text-right">
          {actionRulesEmpty ? null : (
            <Button onClick={() => setAdding(true)}>Add Action Rule</Button>
          )}
        </Col>
      </Row>
      <Row className="mt-3">
        <Col>
          <p>
            ActionRules instruct HMA to take an action when a match meets a set
            of conditions.
          </p>
        </Col>
      </Row>
      <Row>
        {actionRulesEmpty && !adding ? (
          <EmptyState>
            <EmptyState.Lead>
              You have not added action rules yet. Add one using the button
              below.
            </EmptyState.Lead>
            <EmptyState.CTA onClick={() => setAdding(true)}>
              Add Action Rule
            </EmptyState.CTA>
          </EmptyState>
        ) : null}
        <Col>
          <Table>
            {actionRules.length > 0 ? (
              <thead>
                <tr>
                  <th>Name and Action Taken</th>
                  <th colSpan={2}>Conditions</th>
                </tr>
              </thead>
            ) : null}

            <tbody>
              {adding ? (
                <ActionRuleRow
                  key={1}
                  actionRule={defaultActionRule}
                  actions={actions}
                  onDeleteActionRule={() => setAdding(false)}
                  onUpdateActionRule={(_, rule) => onAddActionRule(rule)}
                  nameIsUnique={actionRuleNameIsUnique}
                  forceEditing
                />
              ) : null}

              {actionRules.map(actionRule => (
                <ActionRuleRow
                  key={actionRule.name}
                  actionRule={actionRule}
                  actions={actions}
                  onDeleteActionRule={onDeleteActionRule}
                  onUpdateActionRule={onUpdateActionRule}
                  nameIsUnique={actionRuleNameIsUnique}
                />
              ))}
            </tbody>
          </Table>
        </Col>
      </Row>
    </SettingsTabPane>
  );
}
